#!/usr/bin/env python3
"""Build the Bybit Quantumult X rule set from maintained public sources."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import difflib
import ipaddress
import math
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "rule" / "QuantumultX" / "Bybit" / "Bybit.list"
MANUAL_PATH = ROOT / "data" / "bybit_manual_domains.txt"
EXCLUDED_PATH = ROOT / "data" / "bybit_excluded_domains.txt"
README_PATHS = (
    ROOT / "README.md",
    ROOT / "rule" / "QuantumultX" / "Bybit" / "README.md",
)

AUTHOR = "bluelittlerain"
REPOSITORY_URL = "https://github.com/bluelittlerain/quantumultx-bybit-rules"
USER_AGENT = "quantumultx-bybit-rules-updater/1.0 (+https://github.com/bluelittlerain/quantumultx-bybit-rules)"
NETWORK_TIMEOUT_SECONDS = 20
MINIMUM_UPSTREAM_RULES = 8

# Try the known current layout first, then historical/possible layouts. A 404
# advances to the next candidate; malformed content never silently falls back.
UPSTREAM_CANDIDATES = (
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/bybit.yaml",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/classical/bybit.yaml",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/master/geo/geosite/bybit.yaml",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/master/geo/classical/bybit.yaml",
)

TYPE_ORDER = {
    "HOST": 0,
    "HOST-SUFFIX": 1,
    "IP-CIDR": 2,
    "IP6-CIDR": 3,
}

TYPE_ALIASES = {
    "DOMAIN": "HOST",
    "DOMAIN-SUFFIX": "HOST-SUFFIX",
    "IP-CIDR": "IP-CIDR",
    "IP-CIDR6": "IP6-CIDR",
    "IP6-CIDR": "IP6-CIDR",
    "HOST": "HOST",
    "HOST-SUFFIX": "HOST-SUFFIX",
}

FORBIDDEN_SHARED_ROOTS = frozenset(
    {
        "amazon.com",
        "amazonaws.com",
        "cloudfront.net",
        "cloudflare.com",
        "google.com",
        "googleapis.com",
        "gstatic.com",
        "app-measurement.com",
        "appsflyer.com",
        "firebaseio.com",
        "sentry.io",
        "akamai.net",
        "akamaiedge.net",
        "apple.com",
        "icloud.com",
    }
)

DOMAIN_RE = re.compile(
    r"(?=^.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$",
    re.IGNORECASE,
)


class UpdateError(RuntimeError):
    """Base class for safe update failures."""


class UpstreamError(UpdateError):
    """The upstream source was unavailable or malformed."""


class SafetyError(UpdateError):
    """The candidate output failed a safety invariant."""


@dataclasses.dataclass(frozen=True)
class Rule:
    kind: str
    value: str

    def qx_line(self) -> str:
        return f"{self.kind},{self.value},Bybit"


@dataclasses.dataclass
class UpdateResult:
    source_url: str
    upstream_count: int
    manual_count: int
    excluded_count: int
    old_rules: list[Rule]
    new_rules: list[Rule]
    old_content: str
    new_content: str
    body_changed: bool
    changed: bool
    updated_at: str

    @property
    def added(self) -> list[Rule]:
        return sort_rules(set(self.new_rules) - set(self.old_rules))

    @property
    def removed(self) -> list[Rule]:
        return sort_rules(set(self.old_rules) - set(self.new_rules))


def is_valid_domain(value: str) -> bool:
    return bool(DOMAIN_RE.fullmatch(value))


def normalize_domain(value: str) -> str:
    value = value.strip().strip("\"'").rstrip(".").lower()
    if not is_valid_domain(value):
        raise SafetyError(f"Invalid domain: {value!r}")
    return value


def make_rule(kind: str, value: str) -> Rule:
    canonical_kind = TYPE_ALIASES.get(kind.strip().upper())
    if canonical_kind is None:
        raise SafetyError(f"Unsupported rule type: {kind!r}")

    cleaned = value.strip().strip("\"'")
    if canonical_kind in {"HOST", "HOST-SUFFIX"}:
        cleaned = normalize_domain(cleaned)
    else:
        try:
            network = ipaddress.ip_network(cleaned, strict=False)
        except ValueError as exc:
            raise SafetyError(f"Invalid IP network: {cleaned!r}") from exc
        expected_version = 4 if canonical_kind == "IP-CIDR" else 6
        if network.version != expected_version:
            raise SafetyError(
                f"{canonical_kind} has IPv{network.version} value: {cleaned!r}"
            )
        cleaned = network.with_prefixlen
    return Rule(canonical_kind, cleaned)


def validate_rule_allowed(rule: Rule) -> None:
    if (
        rule.kind in {"HOST", "HOST-SUFFIX"}
        and rule.value in FORBIDDEN_SHARED_ROOTS
    ):
        raise SafetyError(
            f"Forbidden shared service root cannot be routed as Bybit: {rule.qx_line()}"
        )


def _strip_yaml_item(line: str) -> str:
    line = line.strip()
    if line.startswith("-"):
        line = line[1:].strip()
    return line.strip().strip("\"'")


def parse_upstream(text: str) -> list[Rule]:
    validate_upstream_text(text)
    rules: list[Rule] = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line or line in {"payload:", "payload: []"}:
            continue
        line = _strip_yaml_item(line)
        if not line:
            continue

        try:
            upper = line.upper()
            if upper.startswith(tuple(f"{name}," for name in TYPE_ALIASES)):
                parts = [part.strip() for part in line.split(",")]
                if len(parts) < 2:
                    raise SafetyError("missing match value")
                rules.append(make_rule(parts[0], parts[1]))
            elif line.startswith("+."):
                rules.append(make_rule("HOST-SUFFIX", line[2:]))
            elif line.lower().startswith("full:"):
                rules.append(make_rule("HOST", line[5:]))
            elif line.lower().startswith("domain:"):
                rules.append(make_rule("HOST-SUFFIX", line[7:]))
            else:
                # MetaCubeX geosite YAML uses plain values for exact/full domains.
                rules.append(make_rule("HOST", line))
        except SafetyError as exc:
            raise UpstreamError(
                f"Invalid upstream rule at line {line_number}: {exc}"
            ) from exc

    if not rules:
        raise UpstreamError("Upstream contained no usable rules")
    return rules


def validate_upstream_text(text: str) -> None:
    if not text or not text.strip():
        raise UpstreamError("Upstream response was empty")
    sample = text.lstrip().lower()
    html_markers = ("<!doctype html", "<html", "<head", "<body")
    if sample.startswith(html_markers) or any(marker in sample[:1024] for marker in html_markers):
        raise UpstreamError("Upstream returned HTML instead of a rule file")


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain, application/yaml, text/yaml, */*;q=0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT_SECONDS) as response:
        data = response.read()
        content_type = response.headers.get_content_type()
    if content_type == "text/html":
        raise UpstreamError(f"Upstream returned HTML content type: {url}")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UpstreamError(f"Upstream was not UTF-8: {url}") from exc


def locate_upstream(
    candidates: Sequence[str] = UPSTREAM_CANDIDATES,
    opener: Callable[[str], str] = fetch_url,
) -> tuple[str, str]:
    errors: list[str] = []
    for url in candidates:
        try:
            text = opener(url)
        except urllib.error.HTTPError as exc:
            errors.append(f"{url}: HTTP {exc.code}")
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {exc}")
            continue
        validate_upstream_text(text)
        return url, text
    details = "\n".join(f"  - {error}" for error in errors)
    raise UpstreamError(f"No usable MetaCubeX Bybit source was found:\n{details}")


def parse_manual_file(path: Path) -> list[Rule]:
    if not path.is_file():
        raise UpdateError(f"Manual domain file does not exist: {path}")
    rules: list[Rule] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",", 2)]
        if len(parts) < 2:
            raise UpdateError(f"{path}:{line_number}: expected TYPE,value,source")
        try:
            rules.append(make_rule(parts[0], parts[1]))
        except SafetyError as exc:
            raise UpdateError(f"{path}:{line_number}: {exc}") from exc
    return rules


def load_exclusions(path: Path) -> set[str]:
    if not path.is_file():
        raise UpdateError(f"Exclusion file does not exist: {path}")
    exclusions: set[str] = set()
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",", 2)]
        value = parts[1] if len(parts) >= 2 else parts[0]
        try:
            exclusions.add(normalize_domain(value))
        except SafetyError as exc:
            raise UpdateError(f"{path}:{line_number}: {exc}") from exc
    return exclusions


def is_excluded(rule: Rule, exclusions: set[str]) -> bool:
    if rule.kind not in {"HOST", "HOST-SUFFIX"}:
        return False
    return any(
        rule.value == excluded or rule.value.endswith(f".{excluded}")
        for excluded in exclusions
    )


def collapse_parent_coverage(rules: Iterable[Rule]) -> list[Rule]:
    unique = set(rules)
    suffixes = sorted(
        (rule for rule in unique if rule.kind == "HOST-SUFFIX"),
        key=lambda rule: (rule.value.count("."), rule.value.casefold()),
    )
    kept_suffixes: list[Rule] = []
    for rule in suffixes:
        if any(
            rule.value == parent.value or rule.value.endswith(f".{parent.value}")
            for parent in kept_suffixes
        ):
            continue
        kept_suffixes.append(rule)

    kept_suffix_values = {rule.value for rule in kept_suffixes}
    kept: set[Rule] = set(kept_suffixes)
    for rule in unique:
        if rule.kind == "HOST" and any(
            rule.value == suffix or rule.value.endswith(f".{suffix}")
            for suffix in kept_suffix_values
        ):
            continue
        if rule.kind != "HOST-SUFFIX":
            kept.add(rule)
    return sort_rules(kept)


def process_rules(rules: Iterable[Rule]) -> list[Rule]:
    normalized = {make_rule(rule.kind, rule.value) for rule in rules}
    for rule in normalized:
        validate_rule_allowed(rule)
    return collapse_parent_coverage(normalized)


def _rule_sort_key(rule: Rule) -> tuple[object, ...]:
    if rule.kind in {"HOST", "HOST-SUFFIX"}:
        value_key: object = rule.value.casefold()
    else:
        network = ipaddress.ip_network(rule.value, strict=False)
        value_key = (network.version, int(network.network_address), network.prefixlen)
    return (TYPE_ORDER[rule.kind], value_key)


def sort_rules(rules: Iterable[Rule]) -> list[Rule]:
    return sorted(rules, key=_rule_sort_key)


def parse_qx_body(text: str) -> list[Rule]:
    rules: list[Rule] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 3 or parts[2] != "Bybit":
            raise SafetyError(
                f"Invalid existing Quantumult X rule at line {line_number}: {line!r}"
            )
        rules.append(make_rule(parts[0], parts[1]))
    return rules


def serialize_body(rules: Sequence[Rule]) -> str:
    return "\n".join(rule.qx_line() for rule in rules)


def count_rules(rules: Sequence[Rule]) -> dict[str, int]:
    counts = {kind: 0 for kind in TYPE_ORDER}
    for rule in rules:
        counts[rule.kind] += 1
    counts["TOTAL"] = len(rules)
    return counts


def render_rule_file(rules: Sequence[Rule], updated_at: str) -> str:
    counts = count_rules(rules)
    header = [
        "# NAME: Bybit",
        f"# AUTHOR: {AUTHOR}",
        f"# REPO: {REPOSITORY_URL}",
        "# SOURCE: Bybit official documentation, MetaCubeX/meta-rules-dat",
        f"# UPDATED: {updated_at}",
        f"# HOST: {counts['HOST']}",
        f"# HOST-SUFFIX: {counts['HOST-SUFFIX']}",
        f"# IP-CIDR: {counts['IP-CIDR']}",
        f"# IP6-CIDR: {counts['IP6-CIDR']}",
        f"# TOTAL: {counts['TOTAL']}",
        "",
    ]
    return "\n".join(header) + serialize_body(rules) + "\n"


def extract_updated_at(text: str) -> str | None:
    match = re.search(r"^# UPDATED:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def utc_timestamp(now: dt.datetime | None = None) -> str:
    if now is None:
        now = dt.datetime.now(dt.timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    return now.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def enforce_count_safety(
    upstream_rules: Sequence[Rule],
    new_rules: Sequence[Rule],
    existing_rules: Sequence[Rule],
    minimum_upstream: int = MINIMUM_UPSTREAM_RULES,
) -> None:
    if len(upstream_rules) < minimum_upstream:
        raise SafetyError(
            f"Upstream rule count {len(upstream_rules)} is below minimum "
            f"{minimum_upstream}"
        )
    minimum_final = max(8, math.ceil(len(existing_rules) * 0.60))
    if len(new_rules) < minimum_final:
        raise SafetyError(
            f"Candidate final count {len(new_rules)} is below safety floor "
            f"{minimum_final} (max of 8 and 60% of existing {len(existing_rules)})"
        )


def prepare_update(
    *,
    output_path: Path = OUTPUT_PATH,
    manual_path: Path = MANUAL_PATH,
    excluded_path: Path = EXCLUDED_PATH,
    fetcher: Callable[[], tuple[str, str]] = locate_upstream,
    now: dt.datetime | None = None,
    minimum_upstream: int = MINIMUM_UPSTREAM_RULES,
) -> UpdateResult:
    # Fetch and validate everything before considering any write.
    source_url, upstream_text = fetcher()
    upstream_rules = process_rules(parse_upstream(upstream_text))
    manual_rules = process_rules(parse_manual_file(manual_path))
    exclusions = load_exclusions(excluded_path)

    merged = list(upstream_rules) + list(manual_rules)
    allowed: list[Rule] = []
    excluded_count = 0
    for rule in merged:
        if is_excluded(rule, exclusions):
            excluded_count += 1
            continue
        allowed.append(rule)
    new_rules = process_rules(allowed)

    old_content = ""
    old_rules: list[Rule] = []
    if output_path.is_file():
        old_content = output_path.read_text(encoding="utf-8")
        old_rules = process_rules(parse_qx_body(old_content))

    enforce_count_safety(
        upstream_rules,
        new_rules,
        old_rules,
        minimum_upstream=minimum_upstream,
    )

    body_changed = serialize_body(old_rules) != serialize_body(new_rules)
    previous_updated = extract_updated_at(old_content)
    updated_at = (
        utc_timestamp(now)
        if body_changed or previous_updated is None
        else previous_updated
    )
    new_content = render_rule_file(new_rules, updated_at)
    return UpdateResult(
        source_url=source_url,
        upstream_count=len(upstream_rules),
        manual_count=len(manual_rules),
        excluded_count=excluded_count,
        old_rules=old_rules,
        new_rules=new_rules,
        old_content=old_content,
        new_content=new_content,
        body_changed=body_changed,
        changed=new_content != old_content,
        updated_at=updated_at,
    )


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_name = handle.name
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def render_readme(text: str, rules: Sequence[Rule], updated_at: str) -> str:
    counts = count_rules(rules)
    count_text = (
        f"{counts['TOTAL']} 条（HOST {counts['HOST']}，"
        f"HOST-SUFFIX {counts['HOST-SUFFIX']}，"
        f"IP-CIDR {counts['IP-CIDR']}，IP6-CIDR {counts['IP6-CIDR']}）"
    )
    replacements = (
        (
            r"<!-- BYBIT_COUNTS_START -->.*?<!-- BYBIT_COUNTS_END -->",
            f"<!-- BYBIT_COUNTS_START -->{count_text}<!-- BYBIT_COUNTS_END -->",
        ),
        (
            r"<!-- BYBIT_UPDATED_START -->.*?<!-- BYBIT_UPDATED_END -->",
            f"<!-- BYBIT_UPDATED_START -->{updated_at}<!-- BYBIT_UPDATED_END -->",
        ),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    return text


def readme_updates(
    result: UpdateResult,
    paths: Sequence[Path] = README_PATHS,
) -> list[tuple[Path, str, str]]:
    updates: list[tuple[Path, str, str]] = []
    for path in paths:
        if not path.is_file():
            raise UpdateError(f"README file does not exist: {path}")
        old_text = path.read_text(encoding="utf-8")
        new_text = render_readme(old_text, result.new_rules, result.updated_at)
        if "BYBIT_COUNTS_START" not in new_text:
            raise UpdateError(f"README count marker is missing: {path}")
        if path.name == "README.md" and path.parent.name == "Bybit":
            if "BYBIT_UPDATED_START" not in new_text:
                raise UpdateError(f"README update marker is missing: {path}")
        updates.append((path, old_text, new_text))
    return updates


def print_diff(path: Path, old: str, new: str) -> None:
    if old == new:
        return
    for line in difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=f"a/{path.relative_to(ROOT).as_posix()}",
        tofile=f"b/{path.relative_to(ROOT).as_posix()}",
        lineterm="",
    ):
        print(line)


def print_summary(result: UpdateResult, changed: bool, verbose: bool) -> None:
    print(f"Upstream source: {result.source_url}")
    print(f"Upstream rules: {result.upstream_count}")
    print(f"Manual rules: {result.manual_count}")
    print(f"Excluded rules: {result.excluded_count}")
    print(f"Added rules: {len(result.added)}")
    print(f"Removed rules: {len(result.removed)}")
    print(f"Final rules: {len(result.new_rules)}")
    print(f"File changed: {'yes' if changed else 'no'}")
    if verbose:
        for rule in result.added:
            print(f"  + {rule.qx_line()}")
        for rule in result.removed:
            print(f"  - {rule.qx_line()}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="check whether tracked output needs an update; exit 1 when it does",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="show the proposed diff without writing files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show added and removed rules",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        result = prepare_update()
        readmes = readme_updates(result)
        any_changed = result.changed or any(old != new for _, old, new in readmes)

        if args.dry_run:
            print_diff(OUTPUT_PATH, result.old_content, result.new_content)
            for path, old_text, new_text in readmes:
                print_diff(path, old_text, new_text)
        elif not args.check and any_changed:
            if result.changed:
                atomic_write_text(OUTPUT_PATH, result.new_content)
            for path, old_text, new_text in readmes:
                if old_text != new_text:
                    atomic_write_text(path, new_text)

        print_summary(result, any_changed, args.verbose)
        if args.check and any_changed:
            return 1
        return 0
    except UpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Keep scheduled updates safely non-destructive.
        print(f"ERROR: unexpected update failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
