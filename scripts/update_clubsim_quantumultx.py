#!/usr/bin/env python3
"""Build the ClubSim Quantumult X rule sets from approved public data."""

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
AUTHOR = "bluelittlerain"
REPOSITORY_URL = "https://github.com/bluelittlerain/quantumultx-bybit-rules"
USER_AGENT = (
    "quantumultx-clubsim-rules-updater/1.0 "
    "(+https://github.com/bluelittlerain/quantumultx-bybit-rules)"
)
NETWORK_TIMEOUT_SECONDS = 25
UPSTREAM_URL = (
    "https://raw.githubusercontent.com/ClearLuv/iOS_collecton/"
    "main/Rule/ClubSim.list"
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
    "HOST": "HOST",
    "HOST-SUFFIX": "HOST-SUFFIX",
    "IP-CIDR": "IP-CIDR",
    "IP-CIDR6": "IP6-CIDR",
    "IP6-CIDR": "IP6-CIDR",
}

FORBIDDEN_SHARED_ROOTS = frozenset(
    {
        "akamai.net",
        "akamaiedge.net",
        "amazon.com",
        "amazonaws.com",
        "apple.com",
        "appsflyer.com",
        "cloudflare.com",
        "cloudfront.net",
        "doubleclick.net",
        "facebook.com",
        "facebook.net",
        "firebaseapp.com",
        "firebaseio.com",
        "google-analytics.com",
        "google.com",
        "googleapis.com",
        "googleusercontent.com",
        "googletagmanager.com",
        "gstatic.com",
        "hkcsl.com",
        "hkt.com",
        "icloud.com",
        "mastercard.com",
        "mzstatic.com",
        "paypal.com",
        "pccw.com",
        "sentry.io",
        "stripe.com",
        "theclub.com.hk",
        "visa.com",
        "whatsapp.com",
    }
)

NETWORK_DOMAINS = frozenset(
    {
        "csl.prod.ondemandconnectivity.com",
        "hhk.prod.ondemandconnectivity.com",
        "epdg.epc.mnc000.mcc454.pub.3gppnetwork.org",
        "ss.epdg.epc.mnc000.mcc454.pub.3gppnetwork.org",
        "ss.epdg.epc.geo.mnc000.mcc454.pub.3gppnetwork.org",
    }
)

DOMAIN_RE = re.compile(
    r"(?=^.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$",
    re.IGNORECASE,
)
UPDATED_RE = re.compile(r"^# UPDATED:\s*(.*?)\s*$", re.MULTILINE)


class UpdateError(RuntimeError):
    """Base class for safe update failures."""


class UpstreamError(UpdateError):
    """A public upstream was unavailable or malformed."""


class SafetyError(UpdateError):
    """A candidate output failed a safety invariant."""


@dataclasses.dataclass(frozen=True)
class Rule:
    kind: str
    value: str

    def qx_line(self) -> str:
        return f"{self.kind},{self.value},ClubSim"


@dataclasses.dataclass(frozen=True)
class ProjectPaths:
    main_rule: Path
    network_rule: Path
    manual: Path
    network_data: Path
    excluded: Path
    candidates: Path
    readmes: tuple[Path, ...]


@dataclasses.dataclass
class RuleFileUpdate:
    path: Path
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


@dataclasses.dataclass
class ProjectUpdate:
    upstream_count: int
    verified_upstream_count: int
    approved_count: int
    excluded_count: int
    monthly_candidate_count: int
    main: RuleFileUpdate
    network: RuleFileUpdate
    readme_changes: dict[Path, str]

    @property
    def changed(self) -> bool:
        return self.main.changed or self.network.changed or bool(self.readme_changes)

    @property
    def added_count(self) -> int:
        return len(self.main.added) + len(self.network.added)

    @property
    def removed_count(self) -> int:
        return len(self.main.removed) + len(self.network.removed)


def default_paths(root: Path = ROOT) -> ProjectPaths:
    return ProjectPaths(
        main_rule=root / "rule" / "QuantumultX" / "ClubSim" / "ClubSim.list",
        network_rule=(
            root / "rule" / "QuantumultX" / "ClubSim" / "ClubSim-Network.list"
        ),
        manual=root / "data" / "clubsim_manual_domains.txt",
        network_data=root / "data" / "clubsim_network_domains.txt",
        excluded=root / "data" / "clubsim_excluded_domains.txt",
        candidates=root / "data" / "clubsim_candidates.tsv",
        readmes=(
            root / "README.md",
            root / "rule" / "QuantumultX" / "ClubSim" / "README.md",
        ),
    )


def is_valid_domain(value: str) -> bool:
    return bool(DOMAIN_RE.fullmatch(value))


def normalize_domain(value: str) -> str:
    cleaned = value.strip().strip("\"'").rstrip(".").lower()
    if not is_valid_domain(cleaned):
        raise SafetyError(f"Invalid domain: {cleaned!r}")
    return cleaned


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
    if rule.kind not in {"HOST", "HOST-SUFFIX"}:
        return
    if rule.value in FORBIDDEN_SHARED_ROOTS:
        raise SafetyError(
            "Forbidden shared service root cannot be routed as ClubSim: "
            f"{rule.qx_line()}"
        )
    if rule.kind == "HOST-SUFFIX" and any(
        rule.value == root or rule.value.endswith(f".{root}")
        for root in FORBIDDEN_SHARED_ROOTS
    ):
        raise SafetyError(
            "Shared-service suffix cannot be routed as ClubSim: "
            f"{rule.qx_line()}"
        )


def validate_upstream_text(text: str) -> None:
    if not text or not text.strip():
        raise UpstreamError("Upstream response was empty")
    sample = text.lstrip().lower()
    html_markers = ("<!doctype html", "<html", "<head", "<body")
    if sample.startswith(html_markers) or any(
        marker in sample[:2048] for marker in html_markers
    ):
        raise UpstreamError("Upstream returned HTML instead of a rule file")


def parse_upstream(text: str) -> list[Rule]:
    validate_upstream_text(text)
    rules: list[Rule] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-"):
            line = line[1:].strip()
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            continue
        try:
            rules.append(make_rule(parts[0], parts[1]))
        except SafetyError as exc:
            raise UpstreamError(
                f"Invalid upstream rule at line {line_number}: {exc}"
            ) from exc
    if not rules:
        raise UpstreamError("Upstream contained no usable rules")
    return deduplicate_rules(rules)


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain, */*;q=0.1",
        },
    )
    try:
        with urllib.request.urlopen(
            request, timeout=NETWORK_TIMEOUT_SECONDS
        ) as response:
            data = response.read()
            content_type = response.headers.get_content_type()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpstreamError(f"Unable to download public upstream: {exc}") from exc
    if content_type == "text/html":
        raise UpstreamError("Upstream returned an HTML content type")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UpstreamError("Upstream was not UTF-8") from exc


def parse_approved_data(text: str, expected_scope: str) -> list[Rule]:
    rules: list[Rule] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",", 3)]
        if len(parts) != 4:
            raise SafetyError(
                f"Approved data line {line_number} must have four columns"
            )
        kind, value, scope, source = parts
        if scope != expected_scope:
            raise SafetyError(
                f"Approved data line {line_number} has scope {scope!r}; "
                f"expected {expected_scope!r}"
            )
        if not source:
            raise SafetyError(
                f"Approved data line {line_number} is missing source evidence"
            )
        rule = make_rule(kind, value)
        validate_rule_allowed(rule)
        rules.append(rule)
    if not rules:
        raise SafetyError(f"No approved {expected_scope} rules were found")
    return collapse_parent_coverage(deduplicate_rules(rules))


def parse_exclusions(text: str) -> set[str]:
    exclusions: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",", 1)]
        if len(parts) != 2 or not parts[1]:
            raise SafetyError(
                f"Exclusion line {line_number} must contain a value and reason"
            )
        exclusions.add(normalize_domain(parts[0]))
    return exclusions


def count_monthly_candidates(path: Path) -> int:
    if not path.is_file():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return 0
    header = lines[0].split("\t")
    try:
        scope_index = header.index("scope")
    except ValueError:
        return 0
    count = 0
    for line in lines[1:]:
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) > scope_index and fields[scope_index] == "monthly-app":
            count += 1
    return count


def apply_exclusions(rules: Iterable[Rule], exclusions: set[str]) -> list[Rule]:
    return [rule for rule in rules if rule.value not in exclusions]


def deduplicate_rules(rules: Iterable[Rule]) -> list[Rule]:
    unique: dict[tuple[str, str], Rule] = {}
    for rule in rules:
        unique[(rule.kind, rule.value.casefold())] = rule
    return list(unique.values())


def collapse_parent_coverage(rules: Iterable[Rule]) -> list[Rule]:
    unique = deduplicate_rules(rules)
    suffixes = {
        rule.value for rule in unique if rule.kind == "HOST-SUFFIX"
    }
    collapsed: list[Rule] = []
    for rule in unique:
        if rule.kind in {"HOST", "HOST-SUFFIX"}:
            parents = {
                suffix
                for suffix in suffixes
                if suffix != rule.value and rule.value.endswith(f".{suffix}")
            }
            if parents:
                continue
            if rule.kind == "HOST" and rule.value in suffixes:
                continue
        collapsed.append(rule)
    return sort_rules(collapsed)


def _ip_sort_key(value: str) -> tuple[int, int]:
    network = ipaddress.ip_network(value, strict=False)
    return int(network.network_address), network.prefixlen


def sort_rules(rules: Iterable[Rule]) -> list[Rule]:
    def key(rule: Rule) -> tuple[object, ...]:
        if rule.kind in {"IP-CIDR", "IP6-CIDR"}:
            return TYPE_ORDER[rule.kind], *_ip_sort_key(rule.value)
        return TYPE_ORDER[rule.kind], rule.value.casefold()

    return sorted(rules, key=key)


def count_rules(rules: Sequence[Rule]) -> dict[str, int]:
    counts = {kind: 0 for kind in TYPE_ORDER}
    for rule in rules:
        counts[rule.kind] += 1
    counts["TOTAL"] = sum(counts.values())
    return counts


def parse_qx_rules(text: str) -> list[Rule]:
    rules: list[Rule] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 3 or parts[2] != "ClubSim":
            raise SafetyError(
                f"Existing rule line {line_number} is not canonical ClubSim syntax"
            )
        rules.append(make_rule(parts[0], parts[1]))
    return rules


def extract_updated_at(text: str) -> str | None:
    match = UPDATED_RE.search(text)
    return match.group(1) if match else None


def rule_body(rules: Sequence[Rule]) -> str:
    return "\n".join(rule.qx_line() for rule in rules)


def render_rule_file(
    *,
    name: str,
    description: str,
    source: str,
    rules: Sequence[Rule],
    old_content: str,
    now: dt.datetime | None = None,
) -> tuple[str, bool, str]:
    old_rules = parse_qx_rules(old_content) if old_content.strip() else []
    body_changed = rule_body(old_rules) != rule_body(rules)
    old_updated = extract_updated_at(old_content)
    if body_changed or not old_updated:
        timestamp = (now or dt.datetime.now(dt.timezone.utc)).astimezone(
            dt.timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        timestamp = old_updated

    counts = count_rules(rules)
    lines = [
        f"# NAME: {name}",
        f"# DESCRIPTION: {description}",
        f"# AUTHOR: {AUTHOR}",
        f"# REPO: {REPOSITORY_URL}",
        f"# SOURCE: {source}",
        f"# UPDATED: {timestamp}",
        f"# HOST: {counts['HOST']}",
        f"# HOST-SUFFIX: {counts['HOST-SUFFIX']}",
        f"# IP-CIDR: {counts['IP-CIDR']}",
        f"# IP6-CIDR: {counts['IP6-CIDR']}",
        f"# TOTAL: {counts['TOTAL']}",
        "",
        *[rule.qx_line() for rule in rules],
        "",
    ]
    return "\n".join(lines), body_changed, timestamp


def ensure_safe_count(
    *,
    label: str,
    new_rules: Sequence[Rule],
    old_rules: Sequence[Rule],
    absolute_minimum: int,
) -> None:
    required = absolute_minimum
    if old_rules:
        required = max(required, math.ceil(len(old_rules) * 0.60))
    if len(new_rules) < required:
        raise SafetyError(
            f"{label} output has {len(new_rules)} rules; safety floor is {required}"
        )


def _read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    except UnicodeDecodeError as exc:
        raise SafetyError(f"{path} is not valid UTF-8") from exc


def _counts_marker(prefix: str, rules: Sequence[Rule]) -> str:
    counts = count_rules(rules)
    return (
        f"<!-- {prefix}_COUNTS_START -->{counts['TOTAL']} 条"
        f"（HOST {counts['HOST']}，HOST-SUFFIX {counts['HOST-SUFFIX']}，"
        f"IP-CIDR {counts['IP-CIDR']}，IP6-CIDR {counts['IP6-CIDR']}）"
        f"<!-- {prefix}_COUNTS_END -->"
    )


def update_readme_text(
    text: str,
    *,
    main_rules: Sequence[Rule],
    network_rules: Sequence[Rule],
    main_updated: str,
    network_updated: str,
) -> str:
    replacements = {
        "CLUBSIM_MAIN": _counts_marker("CLUBSIM_MAIN", main_rules),
        "CLUBSIM_NETWORK": _counts_marker("CLUBSIM_NETWORK", network_rules),
    }
    updated = text
    for prefix, replacement in replacements.items():
        pattern = re.compile(
            rf"<!-- {prefix}_COUNTS_START -->.*?"
            rf"<!-- {prefix}_COUNTS_END -->",
            re.DOTALL,
        )
        if pattern.search(updated):
            updated = pattern.sub(replacement, updated)
    time_replacements = {
        "CLUBSIM_MAIN": main_updated,
        "CLUBSIM_NETWORK": network_updated,
    }
    for prefix, value in time_replacements.items():
        pattern = re.compile(
            rf"<!-- {prefix}_UPDATED_START -->.*?"
            rf"<!-- {prefix}_UPDATED_END -->",
            re.DOTALL,
        )
        replacement = (
            f"<!-- {prefix}_UPDATED_START -->{value}"
            f"<!-- {prefix}_UPDATED_END -->"
        )
        if pattern.search(updated):
            updated = pattern.sub(replacement, updated)
    return updated


def build_update(
    *,
    paths: ProjectPaths | None = None,
    fetcher: Callable[[str], str] = fetch_url,
    now: dt.datetime | None = None,
) -> ProjectUpdate:
    paths = paths or default_paths()
    manual_text = _read_utf8(paths.manual)
    network_text = _read_utf8(paths.network_data)
    excluded_text = _read_utf8(paths.excluded)
    if not manual_text or not network_text or not excluded_text:
        raise SafetyError("Required approved data files are missing or empty")

    app_rules = parse_approved_data(manual_text, "prepaid-app")
    approved_network_rules = parse_approved_data(network_text, "network")
    exclusions = parse_exclusions(excluded_text)
    app_rules = apply_exclusions(app_rules, exclusions)
    approved_network_rules = apply_exclusions(approved_network_rules, exclusions)

    upstream_rules = parse_upstream(fetcher(UPSTREAM_URL))
    if len(upstream_rules) < 5:
        raise UpstreamError(
            f"Public upstream contains only {len(upstream_rules)} rules; expected at least 5"
        )
    upstream_values = {rule.value for rule in upstream_rules}
    verified_count = sum(
        rule.value in upstream_values for rule in approved_network_rules
    )
    required_verified = max(3, math.ceil(len(approved_network_rules) * 0.60))
    if verified_count < required_verified:
        raise UpstreamError(
            f"Only {verified_count} approved network rules remain in the public "
            f"upstream; safety floor is {required_verified}"
        )

    app_rules = collapse_parent_coverage(app_rules)
    network_rules = collapse_parent_coverage(approved_network_rules)
    for rule in app_rules + network_rules:
        validate_rule_allowed(rule)
    if any(rule.value in NETWORK_DOMAINS for rule in app_rules):
        raise SafetyError("Network-service domains must not enter ClubSim.list")

    old_main_content = _read_utf8(paths.main_rule)
    old_network_content = _read_utf8(paths.network_rule)
    old_main_rules = parse_qx_rules(old_main_content) if old_main_content else []
    old_network_rules = (
        parse_qx_rules(old_network_content) if old_network_content else []
    )
    ensure_safe_count(
        label="ClubSim main",
        new_rules=app_rules,
        old_rules=old_main_rules,
        absolute_minimum=1,
    )
    ensure_safe_count(
        label="ClubSim network",
        new_rules=network_rules,
        old_rules=old_network_rules,
        absolute_minimum=5,
    )

    main_content, main_body_changed, main_updated = render_rule_file(
        name="ClubSim",
        description="Club Sim prepaid app account and service rules",
        source="Club Sim official website and official app static resources",
        rules=app_rules,
        old_content=old_main_content,
        now=now,
    )
    network_content, network_body_changed, network_updated = render_rule_file(
        name="ClubSim Network",
        description="Club Sim optional eSIM, ePDG and network-service rules",
        source="ClearLuv/iOS_collecton ClubSim public rule",
        rules=network_rules,
        old_content=old_network_content,
        now=now,
    )

    main_update = RuleFileUpdate(
        path=paths.main_rule,
        old_rules=old_main_rules,
        new_rules=app_rules,
        old_content=old_main_content,
        new_content=main_content,
        body_changed=main_body_changed,
        changed=old_main_content != main_content,
        updated_at=main_updated,
    )
    network_update = RuleFileUpdate(
        path=paths.network_rule,
        old_rules=old_network_rules,
        new_rules=network_rules,
        old_content=old_network_content,
        new_content=network_content,
        body_changed=network_body_changed,
        changed=old_network_content != network_content,
        updated_at=network_updated,
    )

    readme_changes: dict[Path, str] = {}
    for readme in paths.readmes:
        old_text = _read_utf8(readme)
        if not old_text:
            continue
        new_text = update_readme_text(
            old_text,
            main_rules=app_rules,
            network_rules=network_rules,
            main_updated=main_updated,
            network_updated=network_updated,
        )
        if new_text != old_text:
            readme_changes[readme] = new_text

    return ProjectUpdate(
        upstream_count=len(upstream_rules),
        verified_upstream_count=verified_count,
        approved_count=len(app_rules) + len(approved_network_rules),
        excluded_count=len(exclusions),
        monthly_candidate_count=count_monthly_candidates(paths.candidates),
        main=main_update,
        network=network_update,
        readme_changes=readme_changes,
    )


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def write_update(update: ProjectUpdate) -> None:
    pending: dict[Path, str] = {}
    if update.main.changed:
        pending[update.main.path] = update.main.new_content
    if update.network.changed:
        pending[update.network.path] = update.network.new_content
    pending.update(update.readme_changes)
    for path, content in pending.items():
        atomic_write(path, content)


def print_diff(update: ProjectUpdate) -> None:
    pairs = [
        (update.main.path, update.main.old_content, update.main.new_content),
        (
            update.network.path,
            update.network.old_content,
            update.network.new_content,
        ),
    ]
    for path, old, new in pairs:
        if old == new:
            continue
        print(
            "".join(
                difflib.unified_diff(
                    old.splitlines(keepends=True),
                    new.splitlines(keepends=True),
                    fromfile=f"a/{path.name}",
                    tofile=f"b/{path.name}",
                )
            ),
            end="",
        )


def print_summary(update: ProjectUpdate, *, verbose: bool = False) -> None:
    print(f"Upstream rules: {update.upstream_count}")
    print(f"Verified upstream rules: {update.verified_upstream_count}")
    print(f"Approved domains: {update.approved_count}")
    print(f"App rules: {len(update.main.new_rules)}")
    print(f"Network rules: {len(update.network.new_rules)}")
    print(f"Monthly candidates: {update.monthly_candidate_count}")
    print(f"Exclusions: {update.excluded_count}")
    print(f"Added rules: {update.added_count}")
    print(f"Removed rules: {update.removed_count}")
    print(
        "Final rules: "
        f"{len(update.main.new_rules) + len(update.network.new_rules)}"
    )
    print(f"Changed: {'yes' if update.changed else 'no'}")
    if verbose:
        for label, result in (("main", update.main), ("network", update.network)):
            print(f"{label} updated: {result.updated_at}")
            for rule in result.added:
                print(f"  + {rule.qx_line()}")
            for rule in result.removed:
                print(f"  - {rule.qx_line()}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely update ClubSim Quantumult X rules"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="check whether generated files are current without writing",
    )
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="print generated differences without writing",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="print detailed update information"
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        update = build_update()
        print_summary(update, verbose=args.verbose)
        if args.dry_run:
            print_diff(update)
            return 0
        if args.check:
            if update.changed:
                print("ClubSim generated files need an update.", file=sys.stderr)
                return 1
            return 0
        write_update(update)
        return 0
    except UpdateError as exc:
        print(f"ClubSim update failed safely: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
