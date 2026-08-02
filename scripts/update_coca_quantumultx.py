#!/usr/bin/env python3
"""Safely update the independent COCA Quantumult X resource."""

from __future__ import annotations

import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import quantumultx_rule_utils as utils


ROOT = Path(__file__).resolve().parents[1]
MAXIMUM_SOURCE_BYTES = 8 * 1024 * 1024
COCA_ROOT = "coca.xyz"
DEDICATED_EXTERNAL_HOSTS = frozenset({"wwallet.app.link"})
CONFIG = utils.AppConfig(
    policy="COCA",
    upstream_urls=(
        "https://www.coca.xyz/",
        "https://www.coca.xyz/terms",
        "https://www.coca.xyz/privacy",
        "https://www.coca.xyz/cards",
        "https://www.coca.xyz/blog",
        "https://docs.coca.xyz/",
        "https://help.coca.xyz/",
        "https://status.coca.xyz/",
    ),
    minimum_upstream_rules=2,
    manual_relative="data/coca_manual_domains.txt",
    excluded_relative="data/coca_excluded_domains.txt",
    candidates_relative="data/coca_candidates.tsv",
    readme_relatives=(
        "README.md",
        "rule/QuantumultX/COCA/README.md",
    ),
    outputs=(
        utils.OutputSpec(
            scope="coca-core",
            relative_path="rule/QuantumultX/COCA/COCA.list",
            name="COCA",
            description=(
                "COCA crypto card and wallet official app and service domain rules"
            ),
            source="COCA official sources and reviewed public upstreams",
            minimum_rules=2,
            count_marker="COCA_MAIN_COUNTS",
            updated_marker="COCA_MAIN_UPDATED",
        ),
    ),
    user_agent_component="coca-updater",
    candidate_scopes=(
        "advertising",
        "analytics",
        "authentication",
        "banking",
        "card",
        "classic-wirex",
        "coca-core",
        "exchange",
        "loyalty",
        "nft",
        "recovery",
        "regional",
        "shared-third-party",
        "staking",
        "status",
        "support",
        "transfer",
        "unknown",
        "wallet",
        "walletconnect",
        "web3",
        "wirex-shared",
        "wirexone",
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
    return canonical == COCA_ROOT or canonical.endswith(f".{COCA_ROOT}")


def _approved_observation(host: str) -> list[utils.Rule]:
    """Return only conservative hosts observed on approved official pages."""

    canonical = utils.normalize_domain(host)
    if canonical == COCA_ROOT:
        return [utils.Rule("HOST-SUFFIX", COCA_ROOT)]
    if canonical.endswith(f".{COCA_ROOT}"):
        return [
            utils.Rule("HOST", canonical),
            utils.Rule("HOST-SUFFIX", COCA_ROOT),
        ]
    if canonical in DEDICATED_EXTERNAL_HOSTS:
        return [utils.Rule("HOST", canonical)]
    return []


def fetch_official_observations(url: str, user_agent: str, timeout: int) -> str:
    """Fetch public COCA pages and emit a safe rule-form observation stream."""

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
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                final_url = sanitize_public_url(
                    getattr(response, "geturl", lambda: clean_url)()
                )
                final_host = urllib.parse.urlsplit(final_url).hostname
                if not final_host or not _allowed_source_host(final_host):
                    raise utils.UpstreamError(
                        "official source redirected outside the allowlist"
                    )
                payload = response.read(MAXIMUM_SOURCE_BYTES + 1)
            break
        except utils.UpstreamError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    else:
        raise utils.UpstreamError(
            f"failed to fetch official COCA source {clean_url}: {last_error}"
        ) from last_error

    if len(payload) > MAXIMUM_SOURCE_BYTES:
        raise utils.UpstreamError(f"official source is too large: {clean_url}")
    if "text/html" not in content_type.casefold():
        raise utils.UpstreamError(
            f"official source has unexpected content type {content_type!r}: "
            f"{clean_url}"
        )
    try:
        text = payload.decode("utf-8-sig")
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
    title = re.sub(r"(?is)<[^>]+>", " ", title_match.group(1)).casefold() if title_match else ""
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
    identity_markers = ("wallet", "crypto", "card", "banking")
    if "coca" not in lowered or not any(marker in lowered for marker in identity_markers):
        raise utils.UpstreamError(
            f"official COCA identity marker is missing: {clean_url}"
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


def main() -> int:
    args = utils.build_parser(CONFIG.policy).parse_args()
    if args.check and args.dry_run:
        print("--check and --dry-run cannot be used together", file=sys.stderr)
        return 2
    try:
        plan = utils.prepare_update(
            CONFIG,
            root=ROOT,
            fetcher=fetch_official_observations,
        )
    except utils.RuleError as exc:
        print(f"{CONFIG.policy} update failed: {exc}", file=sys.stderr)
        return 2

    if args.verbose:
        for source_url in CONFIG.upstream_urls:
            print(f"Official source: {sanitize_public_url(source_url)}")
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
