#!/usr/bin/env python3
"""Safely update the independent Wirex One Quantumult X resource."""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import quantumultx_rule_utils as utils
import repository_identity
import resilient_html_sources as resilient


ROOT = Path(__file__).resolve().parents[1]
MAXIMUM_SOURCE_BYTES = 8 * 1024 * 1024
WIREX_ROOT = "wirexapp.com"
DEDICATED_EXTERNAL_HOSTS = frozenset({"wirexone.freshdesk.com"})
CORE_SOURCE_URLS = (
    "https://one.wirexapp.com/",
    "https://www.wirexapp.com/legal/one/terms",
    "https://help.wirexapp.com/article/wirex-one-upgrade-faq-1685",
)
OPTIONAL_SOURCE_URLS = (
    "https://status.wirexapp.com/",
    "https://wirexone.freshdesk.com/support/solutions/76000005022",
)
DISCOVERY_SOURCES = tuple(
    resilient.DiscoverySource(url, "core") for url in CORE_SOURCE_URLS
) + tuple(
    resilient.DiscoverySource(url, "optional") for url in OPTIONAL_SOURCE_URLS
)
MINIMUM_SUCCESSFUL_SOURCES = 2
MINIMUM_CORE_SOURCES = 2
SOURCE_TIMEOUT_SECONDS = 10
CONFIG = utils.AppConfig(
    policy="WirexOne",
    upstream_urls=tuple(source.url for source in DISCOVERY_SOURCES),
    minimum_upstream_rules=2,
    manual_relative="data/wirexone_manual_domains.txt",
    excluded_relative="data/wirexone_excluded_domains.txt",
    candidates_relative="data/wirexone_candidates.tsv",
    readme_relatives=(
        "README.md",
        "rule/QuantumultX/WirexOne/README.md",
    ),
    outputs=(
        utils.OutputSpec(
            scope="wirexone-core",
            relative_path="rule/QuantumultX/WirexOne/WirexOne.list",
            name="WirexOne",
            description="Wirex One official app and service domain rules",
            source="Wirex One official sources and reviewed public upstreams",
            minimum_rules=2,
            count_marker="WIREXONE_MAIN_COUNTS",
            updated_marker="WIREXONE_MAIN_UPDATED",
        ),
    ),
    user_agent_component="wirexone-updater",
    candidate_scopes=(
        "advertising",
        "analytics",
        "banking",
        "blockchain",
        "card",
        "classic-wirex",
        "identity",
        "regional",
        "shared-third-party",
        "status",
        "support",
        "unknown",
        "wallet",
        "wirex-shared-core",
        "wirexone-core",
    ),
)


def sanitize_public_url(url: str) -> str:
    """Remove query and fragment data before requesting or logging a source."""

    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise utils.UpstreamError("official source must be an absolute HTTPS URL")
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path or "/", "", "")
    )


def _allowed_source_host(host: str) -> bool:
    canonical = utils.normalize_domain(host)
    return (
        canonical == WIREX_ROOT
        or canonical.endswith(f".{WIREX_ROOT}")
        or canonical in DEDICATED_EXTERNAL_HOSTS
    )


def _approved_observation(host: str) -> list[utils.Rule]:
    """Return only conservative hosts observed on approved official pages."""

    canonical = utils.normalize_domain(host)
    if canonical == WIREX_ROOT:
        return [utils.Rule("HOST-SUFFIX", WIREX_ROOT)]
    if canonical.endswith(f".{WIREX_ROOT}"):
        return [
            utils.Rule("HOST", canonical),
            utils.Rule("HOST-SUFFIX", WIREX_ROOT),
        ]
    if canonical in DEDICATED_EXTERNAL_HOSTS:
        return [utils.Rule("HOST", canonical)]
    return []


def _validate_discovery_sources() -> None:
    """Treat an invalid configured URL as a hard error, not a skipped source."""

    seen: set[str] = set()
    for source in DISCOVERY_SOURCES:
        clean_url = sanitize_public_url(source.url)
        host = urllib.parse.urlsplit(clean_url).hostname
        if clean_url != source.url:
            raise utils.SafetyError(
                f"configured discovery URL is not canonical: {source.url}"
            )
        if not host or not _allowed_source_host(host):
            raise utils.SafetyError(
                f"configured discovery host is outside the allowlist: {source.url}"
            )
        if clean_url in seen:
            raise utils.SafetyError(
                f"duplicate configured discovery source: {source.url}"
            )
        seen.add(clean_url)


def fetch_official_observations(url: str, user_agent: str, timeout: int) -> str:
    """Fetch public Wirex pages and emit a safe rule-form observation stream."""

    clean_url = sanitize_public_url(url)
    source_host = urllib.parse.urlsplit(clean_url).hostname
    if not source_host or not _allowed_source_host(source_host):
        raise utils.UpstreamError("official source host is outside the allowlist")

    request = urllib.request.Request(
        clean_url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    response = resilient.fetch_html(
        request,
        timeout=timeout,
        maximum_bytes=MAXIMUM_SOURCE_BYTES,
        opener=urllib.request.urlopen,
        sleeper=time.sleep,
    )
    final_url = sanitize_public_url(response.final_url)
    final_host = urllib.parse.urlsplit(final_url).hostname
    if not final_host or not _allowed_source_host(final_host):
        raise utils.UpstreamError(
            "official source redirected outside the allowlist"
        )
    if "text/html" not in response.content_type.casefold():
        raise utils.UpstreamError(
            "official source has unexpected content type "
            f"{response.content_type!r}: "
            f"{clean_url}"
        )
    try:
        text = response.payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise utils.UpstreamError(
            f"official source is not UTF-8: {clean_url}"
        ) from exc

    lowered = text.casefold()
    if len(text) < 1024 or "<html" not in lowered[:4096]:
        raise utils.UpstreamError(
            f"official source is empty or malformed: {clean_url}"
        )
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
    title = (
        re.sub(r"(?is)<[^>]+>", " ", title_match.group(1)).casefold()
        if title_match
        else ""
    )
    error_title_markers = (
        "404",
        "access denied",
        "error",
        "not found",
        "page unavailable",
        "temporarily unavailable",
    )
    if title and any(marker in title for marker in error_title_markers):
        raise utils.UpstreamError(
            f"official source returned an error page: {clean_url}"
        )
    if "wirex" not in lowered:
        raise utils.UpstreamError(
            f"official Wirex identity marker is missing: {clean_url}"
        )

    observations = _approved_observation(source_host)
    normalized = text.replace("\\/", "/")
    for match in re.finditer(
        r"(?i)https?://"
        r"([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
        r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+)",
        normalized,
    ):
        observations.extend(_approved_observation(match.group(1)))

    rules = utils.deduplicate_upstream_rules(observations)
    if not rules:
        raise utils.UpstreamError(
            f"official source contains no approved observations: {clean_url}"
        )
    return "\n".join(
        f"full:{rule.value}" if rule.kind == "HOST" else rule.value
        for rule in rules
    ) + "\n"


def prepare_resilient_update(
    *,
    root: Path = ROOT,
    fetcher: utils.Fetcher = fetch_official_observations,
    now: dt.datetime | None = None,
    timeout: int = SOURCE_TIMEOUT_SECONDS,
) -> tuple[utils.UpdatePlan, resilient.AggregatedSources]:
    """Aggregate healthy official sources before invoking strict generation."""

    _validate_discovery_sources()
    aggregated = resilient.aggregate_observations(
        DISCOVERY_SOURCES,
        fetcher=fetcher,
        user_agent=repository_identity.user_agent(CONFIG.user_agent_component),
        timeout=timeout,
        minimum_successful_sources=MINIMUM_SUCCESSFUL_SOURCES,
        minimum_core_sources=MINIMUM_CORE_SOURCES,
        minimum_observations=CONFIG.minimum_upstream_rules,
    )
    aggregate_config = dataclasses.replace(
        CONFIG,
        upstream_urls=("https://aggregated.invalid/wirexone",),
    )
    plan = utils.prepare_update(
        aggregate_config,
        root=root,
        fetcher=lambda url, user_agent, source_timeout: aggregated.text,
        now=now,
        timeout=timeout,
    )
    return plan, aggregated


def main() -> int:
    args = utils.build_parser(CONFIG.policy).parse_args()
    if args.check and args.dry_run:
        print("--check and --dry-run cannot be used together", file=sys.stderr)
        return 2
    try:
        plan, sources = prepare_resilient_update()
    except utils.RuleError as exc:
        print(f"{CONFIG.policy} update failed: {exc}", file=sys.stderr)
        return 2

    print("Official sources:")
    print(f"successful: {len(sources.successful)}")
    print(
        f"core successful: {sources.core_successful}/"
        f"{sum(source.tier == 'core' for source in DISCOVERY_SOURCES)}"
    )
    print(f"skipped: {sources.skipped}")
    if args.verbose:
        for source in sources.successful:
            print(f"- successful [{source.tier}]: {source.url}")
    if sources.warnings:
        print("Warnings:")
        for warning in sources.warnings:
            print(f"- {warning.source.url}: {warning.reason}")
    print(f"Upstream observations: {plan.upstream_count}")
    print(f"Approved manual rules: {plan.manual_count}")
    print(f"Exclusions: {plan.excluded_count}")
    for item in plan.files:
        if item.final_count:
            print(
                f"{item.path.name}: added={item.added} removed={item.removed} "
                f"final={item.final_count} "
                f"body_changed={'yes' if item.body_changed else 'no'}"
            )
    formal_files = [item for item in plan.files if item.final_count]
    print(
        "Formal rules preserved: "
        + ("yes" if all(item.removed == 0 for item in formal_files) else "no")
    )
    print(f"Files changed: {sum(item.changed for item in plan.files)}")

    if args.dry_run:
        for item in plan.files:
            if item.changed:
                print(utils.format_diff(item, ROOT), end="")
        return 0
    if args.check:
        return 1 if plan.changed else 0
    if plan.changed:
        for item in plan.files:
            if item.changed:
                utils.atomic_write(item.path, item.new_content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
