#!/usr/bin/env python3
"""Update the independent Ether.fi Quantumult X rule resource."""

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
OFFICIAL_EXTERNAL_HOSTS = frozenset({"etherfi.gitbook.io"})
CONFIG = utils.AppConfig(
    policy="EtherFi",
    upstream_urls=(
        "https://www.ether.fi/",
        "https://www.ether.fi/stake",
        "https://www.ether.fi/liquid",
        "https://www.ether.fi/cash",
    ),
    minimum_upstream_rules=2,
    manual_relative="data/etherfi_manual_domains.txt",
    excluded_relative="data/etherfi_excluded_domains.txt",
    candidates_relative="data/etherfi_candidates.tsv",
    readme_relatives=(
        "README.md",
        "rule/QuantumultX/EtherFi/README.md",
    ),
    outputs=(
        utils.OutputSpec(
            scope="main",
            relative_path="rule/QuantumultX/EtherFi/EtherFi.list",
            name="EtherFi",
            description=(
                "Ether.fi official app and core first-party service domain rules"
            ),
            source=(
                "ether.fi official website, Help Center, documentation, "
                "and official app listings"
            ),
            minimum_rules=1,
            count_marker="ETHERFI_MAIN_COUNTS",
            updated_marker="ETHERFI_MAIN_UPDATED",
        ),
    ),
    user_agent_component="etherfi-updater",
)


def _approved_observation(host: str) -> list[utils.Rule]:
    """Return conservative observations for a host found in an official page."""

    canonical = utils.normalize_domain(host)
    if canonical == "ether.fi":
        return [utils.Rule("HOST-SUFFIX", canonical)]
    if canonical.endswith(".ether.fi"):
        return [
            utils.Rule("HOST-SUFFIX", "ether.fi"),
            utils.Rule("HOST", canonical),
        ]
    if canonical in OFFICIAL_EXTERNAL_HOSTS:
        return [utils.Rule("HOST", canonical)]
    return []


def fetch_official_observations(url: str, user_agent: str, timeout: int) -> str:
    """Fetch an official HTML page and emit only first-party domain observations."""

    request = urllib.request.Request(
        url,
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
                payload = response.read(MAXIMUM_SOURCE_BYTES + 1)
            break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    else:
        raise utils.UpstreamError(
            f"failed to fetch official Ether.fi source {url}: {last_error}"
        ) from last_error

    if len(payload) > MAXIMUM_SOURCE_BYTES:
        raise utils.UpstreamError(f"official source is too large: {url}")
    if "text/html" not in content_type.casefold():
        raise utils.UpstreamError(
            f"official source has unexpected content type {content_type!r}: {url}"
        )
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise utils.UpstreamError(f"official source is not UTF-8: {url}") from exc

    lowered = text.casefold()
    if len(text) < 1024 or "<html" not in lowered[:4096]:
        raise utils.UpstreamError(f"official source is empty or malformed: {url}")
    if "ether.fi" not in lowered:
        raise utils.UpstreamError(
            f"official Ether.fi identity marker is missing: {url}"
        )

    source_host = urllib.parse.urlsplit(url).hostname
    if not source_host:
        raise utils.UpstreamError(f"official source URL has no host: {url}")
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
            f"official source contains no approved observations: {url}"
        )
    lines = [
        f"full:{rule.value}" if rule.kind == "HOST" else rule.value
        for rule in rules
    ]
    return "\n".join(lines) + "\n"


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
        for url in CONFIG.upstream_urls:
            print(f"Official source: {url}")
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
