#!/usr/bin/env python3
"""Bounded HTTP retries and safe aggregation for HTML discovery sources.

This module is intentionally opt-in.  Existing application updaters keep the
strict shared ``prepare_update`` behavior unless they explicitly import it.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import email.utils
import http.client
import math
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence

import quantumultx_rule_utils as utils


RETRYABLE_HTTP_STATUS = frozenset({403, 408, 429, *range(500, 600)})
DEFAULT_ATTEMPTS = 3
DEFAULT_MAX_RETRY_AFTER_SECONDS = 10


@dataclasses.dataclass(frozen=True)
class DiscoverySource:
    url: str
    tier: str

    def __post_init__(self) -> None:
        if self.tier not in {"core", "optional"}:
            raise ValueError(f"unsupported discovery source tier: {self.tier!r}")


@dataclasses.dataclass(frozen=True)
class HtmlResponse:
    payload: bytes
    content_type: str
    final_url: str


@dataclasses.dataclass(frozen=True)
class SourceWarning:
    source: DiscoverySource
    reason: str


@dataclasses.dataclass(frozen=True)
class AggregatedSources:
    text: str
    successful: tuple[DiscoverySource, ...]
    warnings: tuple[SourceWarning, ...]
    observation_count: int

    @property
    def core_successful(self) -> int:
        return sum(source.tier == "core" for source in self.successful)

    @property
    def skipped(self) -> int:
        return len(self.warnings)


class SourceFetchError(utils.UpstreamError):
    """A single discovery source failed after a bounded attempt sequence."""

    def __init__(self, reason: str, attempts: int) -> None:
        self.reason = reason
        self.attempts = attempts
        suffix = "attempt" if attempts == 1 else "attempts"
        super().__init__(f"{reason} — skipped after {attempts} {suffix}")


Opener = Callable[..., object]
Sleeper = Callable[[float], None]
ObservationFetcher = Callable[[str, str, int], str]


def _retry_after_seconds(value: str | None) -> int | None:
    if not value:
        return None
    value = value.strip()
    if value.isdecimal():
        return int(value)
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    delta = (parsed - dt.datetime.now(dt.timezone.utc)).total_seconds()
    return max(0, math.ceil(delta))


def _error_reason(error: urllib.error.HTTPError) -> str:
    description = str(error.reason).strip()
    return f"HTTP {error.code}" + (f" {description}" if description else "")


def _retry_delay(
    error: urllib.error.HTTPError,
    *,
    attempt: int,
    max_retry_after_seconds: int,
) -> float:
    retry_after = _retry_after_seconds(
        error.headers.get("Retry-After") if error.headers else None
    )
    if retry_after is None:
        return float(min(attempt, 2))
    if retry_after > max_retry_after_seconds:
        raise SourceFetchError(
            f"{_error_reason(error)}; Retry-After {retry_after}s exceeds "
            f"{max_retry_after_seconds}s limit",
            attempt,
        ) from error
    return float(retry_after)


def fetch_html(
    request: urllib.request.Request,
    *,
    timeout: int,
    maximum_bytes: int,
    opener: Opener = urllib.request.urlopen,
    sleeper: Sleeper,
    attempts: int = DEFAULT_ATTEMPTS,
    max_retry_after_seconds: int = DEFAULT_MAX_RETRY_AFTER_SECONDS,
) -> HtmlResponse:
    """Fetch one HTML source with bounded, status-aware retry handling."""

    if attempts < 1:
        raise ValueError("attempts must be positive")
    if max_retry_after_seconds < 0:
        raise ValueError("max_retry_after_seconds cannot be negative")

    for attempt in range(1, attempts + 1):
        try:
            with opener(request, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                final_url = getattr(response, "geturl", lambda: request.full_url)()
                payload = response.read(maximum_bytes + 1)
            if len(payload) > maximum_bytes:
                raise SourceFetchError("response is too large", attempt)
            return HtmlResponse(payload, content_type, final_url)
        except SourceFetchError:
            raise
        except urllib.error.HTTPError as exc:
            reason = _error_reason(exc)
            if exc.code not in RETRYABLE_HTTP_STATUS or attempt >= attempts:
                raise SourceFetchError(reason, attempt) from exc
            delay = _retry_delay(
                exc,
                attempt=attempt,
                max_retry_after_seconds=max_retry_after_seconds,
            )
            sleeper(delay)
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            http.client.HTTPException,
        ) as exc:
            if attempt >= attempts:
                raise SourceFetchError(
                    f"temporary network error: {exc}", attempt
                ) from exc
            sleeper(float(min(attempt, 2)))

    raise AssertionError("unreachable retry state")


def aggregate_observations(
    sources: Sequence[DiscoverySource],
    *,
    fetcher: ObservationFetcher,
    user_agent: str,
    timeout: int,
    minimum_successful_sources: int,
    minimum_core_sources: int,
    minimum_observations: int,
) -> AggregatedSources:
    """Collect independent sources and enforce source and observation floors."""

    successful: list[DiscoverySource] = []
    warnings: list[SourceWarning] = []
    observations: list[utils.Rule] = []

    for source in sources:
        try:
            text = fetcher(source.url, user_agent, timeout)
            rules = utils.parse_upstream(text)
        except utils.RuleError as exc:
            warnings.append(SourceWarning(source, str(exc)))
            continue
        successful.append(source)
        observations.extend(rules)

    unique = utils.deduplicate_upstream_rules(observations)
    result = AggregatedSources(
        text="".join(f"{rule.kind},{rule.value}\n" for rule in unique),
        successful=tuple(successful),
        warnings=tuple(warnings),
        observation_count=len(unique),
    )

    failures: list[str] = []
    if not result.successful:
        failures.append("all official discovery sources failed")
    if len(result.successful) < minimum_successful_sources:
        failures.append(
            f"successful sources {len(result.successful)} are below safety "
            f"minimum {minimum_successful_sources}"
        )
    if result.core_successful < minimum_core_sources:
        failures.append(
            f"successful core sources {result.core_successful} are below safety "
            f"minimum {minimum_core_sources}"
        )
    if result.observation_count < minimum_observations:
        failures.append(
            f"observation count {result.observation_count} is below safety "
            f"minimum {minimum_observations}"
        )
    if failures:
        warning_summary = "; ".join(
            f"{warning.source.url}: {warning.reason}" for warning in result.warnings
        )
        detail = "; ".join(failures)
        if warning_summary:
            detail += f"; warnings: {warning_summary}"
        raise utils.SafetyError(f"official source safety threshold failed: {detail}")

    return result
