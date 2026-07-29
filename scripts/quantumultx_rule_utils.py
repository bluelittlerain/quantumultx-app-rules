#!/usr/bin/env python3
"""Shared, conservative helpers for maintained Quantumult X rule sets."""

from __future__ import annotations

import argparse
import csv
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
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import repository_identity


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
DOMAIN_RE = re.compile(
    r"(?=^.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$",
    re.IGNORECASE,
)
SINGLE_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
UPDATED_RE = re.compile(r"^# UPDATED:\s*(.*?)\s*$", re.MULTILINE)
HEADER_KEYS = ("HOST", "HOST-SUFFIX", "IP-CIDR", "IP6-CIDR", "TOTAL")
CANDIDATE_HEADER = (
    "domain",
    "rule_type",
    "scope",
    "status",
    "source",
    "evidence",
    "risk",
    "notes",
)
SHARED_ROOTS = frozenset(
    {
        "akamai.net",
        "akamaiedge.net",
        "amazon.com",
        "amazonaws.com",
        "apple.com",
        "appsflyer.com",
        "appsflyersdk.com",
        "azure.com",
        "azureedge.net",
        "cloudflare.com",
        "cloudflare.net",
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
        "icloud.com",
        "live.com",
        "microsoft.com",
        "microsoftonline.com",
        "mzstatic.com",
        "office.com",
        "sentry.io",
        "windows.com",
    }
)


class RuleError(RuntimeError):
    """Base class for parsing, update, and validation failures."""


class UpstreamError(RuleError):
    """A public upstream was unavailable or malformed."""


class SafetyError(RuleError):
    """A proposed rule or output violated a safety invariant."""


@dataclasses.dataclass(frozen=True)
class Rule:
    kind: str
    value: str

    def qx_line(self, policy: str) -> str:
        return f"{self.kind},{self.value},{policy}"


@dataclasses.dataclass(frozen=True)
class ManualRule:
    rule: Rule
    scope: str
    source: str


@dataclasses.dataclass(frozen=True)
class OutputSpec:
    scope: str
    relative_path: str
    name: str
    description: str
    source: str
    minimum_rules: int
    count_marker: str
    updated_marker: str


@dataclasses.dataclass(frozen=True)
class AppConfig:
    policy: str
    upstream_urls: tuple[str, ...]
    minimum_upstream_rules: int
    manual_relative: str
    excluded_relative: str
    candidates_relative: str
    readme_relatives: tuple[str, ...]
    outputs: tuple[OutputSpec, ...]
    user_agent_component: str


@dataclasses.dataclass
class PreparedFile:
    path: Path
    old_content: str
    new_content: str
    body_changed: bool
    added: int = 0
    removed: int = 0
    final_count: int = 0

    @property
    def changed(self) -> bool:
        return self.old_content != self.new_content


@dataclasses.dataclass
class UpdatePlan:
    upstream_count: int
    manual_count: int
    excluded_count: int
    files: list[PreparedFile]

    @property
    def changed(self) -> bool:
        return any(item.changed for item in self.files)


Fetcher = Callable[[str, str, int], str]


def normalize_domain(value: str, *, allow_single_label: bool = False) -> str:
    domain = value.strip().strip("\"'").rstrip(".").casefold()
    if not domain:
        raise SafetyError("empty domain")
    valid = bool(DOMAIN_RE.fullmatch(domain))
    if allow_single_label:
        valid = valid or bool(SINGLE_LABEL_RE.fullmatch(domain))
    if not valid:
        raise SafetyError(f"invalid domain {value!r}")
    return domain


def make_rule(kind: str, value: str) -> Rule:
    normalized_kind = TYPE_ALIASES.get(kind.strip().upper())
    if not normalized_kind:
        raise SafetyError(f"unsupported rule type {kind!r}")
    raw_value = value.strip()
    if normalized_kind in {"HOST", "HOST-SUFFIX"}:
        normalized_value = normalize_domain(raw_value)
    else:
        try:
            network = ipaddress.ip_network(raw_value, strict=False)
        except ValueError as exc:
            raise SafetyError(f"invalid IP network {raw_value!r}") from exc
        if normalized_kind == "IP-CIDR" and network.version != 4:
            raise SafetyError(f"IPv6 network used with IP-CIDR: {raw_value!r}")
        if normalized_kind == "IP6-CIDR" and network.version != 6:
            raise SafetyError(f"IPv4 network used with IP6-CIDR: {raw_value!r}")
        normalized_value = str(network)
    return Rule(normalized_kind, normalized_value)


def _root_match(domain: str, root: str) -> bool:
    return domain == root or domain.endswith(f".{root}")


def validate_rule_allowed(rule: Rule, *, allow_ip: bool = False) -> None:
    if rule.kind in {"IP-CIDR", "IP6-CIDR"}:
        if not allow_ip:
            raise SafetyError("public IP rules are not approved for this rule set")
        network = ipaddress.ip_network(rule.value)
        if not network.is_global:
            raise SafetyError(f"non-global IP network {rule.value!r}")
        return
    for root in SHARED_ROOTS:
        if rule.kind == "HOST-SUFFIX" and _root_match(rule.value, root):
            raise SafetyError(f"shared root cannot be used as HOST-SUFFIX: {rule.value}")
        if rule.kind == "HOST" and rule.value == root:
            raise SafetyError(f"shared root cannot be used as HOST: {rule.value}")


def sort_key(rule: Rule) -> tuple[object, ...]:
    if rule.kind in {"HOST", "HOST-SUFFIX"}:
        value_key: tuple[object, ...] = (rule.value.casefold(),)
    else:
        network = ipaddress.ip_network(rule.value)
        value_key = (network.version, int(network.network_address), network.prefixlen)
    return (TYPE_ORDER[rule.kind], *value_key)


def collapse_parent_coverage(rules: Iterable[Rule]) -> list[Rule]:
    canonical: dict[tuple[str, str], Rule] = {}
    for source_rule in rules:
        rule = make_rule(source_rule.kind, source_rule.value)
        validate_rule_allowed(rule)
        canonical[(rule.kind, rule.value.casefold())] = rule
    suffixes = {
        rule.value
        for rule in canonical.values()
        if rule.kind == "HOST-SUFFIX"
    }
    kept: list[Rule] = []
    for rule in canonical.values():
        if rule.kind not in {"HOST", "HOST-SUFFIX"}:
            kept.append(rule)
            continue
        labels = rule.value.split(".")
        parents = {".".join(labels[index:]) for index in range(1, len(labels))}
        if rule.kind == "HOST":
            parents.add(rule.value)
        if any(parent in suffixes for parent in parents):
            if not (rule.kind == "HOST-SUFFIX" and rule.value in suffixes):
                continue
            if any(parent in suffixes for parent in parents if parent != rule.value):
                continue
        kept.append(rule)
    return sorted(kept, key=sort_key)


def process_rules(rules: Iterable[Rule]) -> list[Rule]:
    return collapse_parent_coverage(rules)


def deduplicate_upstream_rules(rules: Iterable[Rule]) -> list[Rule]:
    """Canonicalize upstream observations without approving shared roots."""

    canonical: dict[tuple[str, str], Rule] = {}
    for source_rule in rules:
        rule = make_rule(source_rule.kind, source_rule.value)
        canonical[(rule.kind, rule.value.casefold())] = rule
    return sorted(canonical.values(), key=sort_key)


def count_rules(rules: Sequence[Rule]) -> dict[str, int]:
    counts = {kind: 0 for kind in TYPE_ORDER}
    for rule in rules:
        counts[rule.kind] += 1
    counts["TOTAL"] = len(rules)
    return counts


def _source_entries(text: str) -> list[str]:
    entries: list[str] = []
    for raw_line in text.replace("\r", "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("payload:"):
            line = line[len("payload:") :].strip()
        parts = re.split(r"\s+-\s+", line)
        if len(parts) > 1:
            if parts[0].startswith("-"):
                parts[0] = parts[0][1:].strip()
            entries.extend(part for part in parts if part)
        else:
            entries.append(line)
    return entries


def parse_upstream(text: str) -> list[Rule]:
    stripped = text.lstrip()
    if not stripped:
        raise UpstreamError("upstream response is empty")
    if stripped.casefold().startswith(("<!doctype html", "<html")):
        raise UpstreamError("upstream returned HTML instead of rules")
    yaml_mode = stripped.startswith("payload:")
    rules: list[Rule] = []
    for raw_entry in _source_entries(text):
        entry = raw_entry.strip().lstrip("-").strip().strip("\"'")
        if not entry or entry in {"payload:", "payload"}:
            continue
        entry = entry.split("#", 1)[0].strip()
        entry = entry.split()[0] if entry else ""
        if not entry:
            continue
        try:
            if "," in entry:
                fields = [field.strip() for field in entry.split(",")]
                if fields[0].upper() in TYPE_ALIASES and len(fields) >= 2:
                    rules.append(make_rule(fields[0], fields[1]))
                continue
            if entry.startswith("full:"):
                rules.append(make_rule("HOST", entry[5:]))
                continue
            if entry.startswith(("+.", ".")):
                suffix_value = entry.lstrip("+.")
                if "." not in suffix_value:
                    continue
                rules.append(make_rule("HOST-SUFFIX", suffix_value))
                continue
            if entry.startswith(("regexp:", "include:", "keyword:")):
                continue
            if "." not in entry:
                continue
            rules.append(make_rule("HOST" if yaml_mode else "HOST-SUFFIX", entry))
        except SafetyError as exc:
            raise UpstreamError(f"invalid upstream entry {raw_entry!r}: {exc}") from exc
    if not rules:
        raise UpstreamError("upstream contains no supported rules")
    return deduplicate_upstream_rules(rules)


def fetch_text(url: str, user_agent: str, timeout: int) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/plain, application/yaml, */*;q=0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            payload = response.read(8 * 1024 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpstreamError(f"failed to fetch public upstream {url}: {exc}") from exc
    if len(payload) > 8 * 1024 * 1024:
        raise UpstreamError(f"upstream response is too large: {url}")
    if "text/html" in content_type.casefold():
        raise UpstreamError(f"upstream returned HTML: {url}")
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UpstreamError(f"upstream is not UTF-8: {url}") from exc


def parse_manual(text: str, allowed_scopes: set[str]) -> list[ManualRule]:
    entries: list[ManualRule] = []
    seen: set[tuple[str, str, str]] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        row = next(csv.reader([line]))
        if len(row) != 4:
            raise SafetyError(
                f"manual data line {line_number}: expected four comma-separated fields"
            )
        kind, value, scope, source = (field.strip() for field in row)
        if scope not in allowed_scopes:
            raise SafetyError(
                f"manual data line {line_number}: unsupported scope {scope!r}"
            )
        rule = make_rule(kind, value)
        validate_rule_allowed(rule)
        key = (scope, rule.kind, rule.value)
        if key in seen:
            raise SafetyError(f"manual data line {line_number}: duplicate rule")
        if not source:
            raise SafetyError(f"manual data line {line_number}: source is empty")
        seen.add(key)
        entries.append(ManualRule(rule, scope, source))
    if not entries:
        raise SafetyError("manual approved-domain data is empty")
    return entries


def parse_exclusions(text: str) -> dict[str, str]:
    exclusions: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        row = next(csv.reader([line]))
        if len(row) != 2:
            raise SafetyError(
                f"exclusion line {line_number}: expected domain and reason"
            )
        domain = normalize_domain(row[0], allow_single_label=True)
        reason = row[1].strip()
        if not reason:
            raise SafetyError(f"exclusion line {line_number}: reason is empty")
        exclusions[domain] = reason
    return exclusions


def is_excluded(rule: Rule, exclusions: Mapping[str, str]) -> bool:
    if rule.kind == "HOST":
        return rule.value in exclusions
    if rule.kind == "HOST-SUFFIX":
        return any(_root_match(rule.value, root) for root in exclusions)
    return False


def apply_exclusions(
    rules: Iterable[Rule], exclusions: Mapping[str, str]
) -> list[Rule]:
    return process_rules(rule for rule in rules if not is_excluded(rule, exclusions))


def parse_rule_body(text: str, policy: str) -> list[Rule]:
    rules: list[Rule] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 3:
            raise SafetyError(f"rule line {line_number}: expected three columns")
        if fields[2] != policy:
            raise SafetyError(
                f"rule line {line_number}: policy must be {policy}, got {fields[2]!r}"
            )
        rules.append(make_rule(fields[0], fields[1]))
    return rules


def extract_updated(text: str) -> str:
    match = UPDATED_RE.search(text)
    return match.group(1) if match else ""


def render_rule_file(
    *,
    spec: OutputSpec,
    policy: str,
    rules: Sequence[Rule],
    old_content: str,
    now: dt.datetime,
) -> tuple[str, bool, str]:
    old_rules = parse_rule_body(old_content, policy) if old_content.strip() else []
    body_changed = old_rules != list(rules)
    previous_updated = extract_updated(old_content)
    if body_changed or not previous_updated:
        updated = now.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        updated = previous_updated
    counts = count_rules(rules)
    lines = [
        f"# NAME: {spec.name}",
        f"# DESCRIPTION: {spec.description}",
        f"# AUTHOR: {repository_identity.OWNER}",
        f"# REPO: {repository_identity.REPOSITORY_URL}",
        f"# SOURCE: {spec.source}",
        f"# UPDATED: {updated}",
        f"# HOST: {counts['HOST']}",
        f"# HOST-SUFFIX: {counts['HOST-SUFFIX']}",
        f"# IP-CIDR: {counts['IP-CIDR']}",
        f"# IP6-CIDR: {counts['IP6-CIDR']}",
        f"# TOTAL: {counts['TOTAL']}",
        "",
    ]
    lines.extend(rule.qx_line(policy) for rule in rules)
    return "\n".join(lines) + "\n", body_changed, updated


def _count_text(rules: Sequence[Rule]) -> str:
    counts = count_rules(rules)
    return (
        f"{counts['TOTAL']} 条（HOST {counts['HOST']}，"
        f"HOST-SUFFIX {counts['HOST-SUFFIX']}，"
        f"IP-CIDR {counts['IP-CIDR']}，IP6-CIDR {counts['IP6-CIDR']}）"
    )


def update_readme_markers(
    text: str,
    output_values: Mapping[str, tuple[OutputSpec, Sequence[Rule], str]],
    *,
    path: Path,
) -> str:
    updated_text = text
    for spec, rules, updated in output_values.values():
        count_pattern = re.compile(
            rf"<!-- {re.escape(spec.count_marker)}_START -->.*?"
            rf"<!-- {re.escape(spec.count_marker)}_END -->"
        )
        count_replacement = (
            f"<!-- {spec.count_marker}_START -->{_count_text(rules)}"
            f"<!-- {spec.count_marker}_END -->"
        )
        if not count_pattern.search(updated_text):
            raise SafetyError(
                f"{path}: missing README marker {spec.count_marker}"
            )
        updated_text = count_pattern.sub(count_replacement, updated_text)
        updated_pattern = re.compile(
            rf"<!-- {re.escape(spec.updated_marker)}_START -->.*?"
            rf"<!-- {re.escape(spec.updated_marker)}_END -->"
        )
        updated_replacement = (
            f"<!-- {spec.updated_marker}_START -->{updated}"
            f"<!-- {spec.updated_marker}_END -->"
        )
        if not updated_pattern.search(updated_text):
            raise SafetyError(
                f"{path}: missing README marker {spec.updated_marker}"
            )
        updated_text = updated_pattern.sub(updated_replacement, updated_text)
    return updated_text


def _read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    except UnicodeDecodeError as exc:
        raise SafetyError(f"{path}: not valid UTF-8") from exc


def prepare_update(
    config: AppConfig,
    *,
    root: Path,
    fetcher: Fetcher = fetch_text,
    now: dt.datetime | None = None,
    timeout: int = 25,
) -> UpdatePlan:
    now = now or dt.datetime.now(dt.timezone.utc)
    user_agent = repository_identity.user_agent(config.user_agent_component)
    upstream_rules: list[Rule] = []
    for url in config.upstream_urls:
        text = fetcher(url, user_agent, timeout)
        upstream_rules.extend(parse_upstream(text))
    upstream = deduplicate_upstream_rules(upstream_rules)
    if len(upstream) < config.minimum_upstream_rules:
        raise SafetyError(
            f"upstream rule count {len(upstream)} is below safety minimum "
            f"{config.minimum_upstream_rules}"
        )

    output_scopes = {spec.scope for spec in config.outputs}
    manual_path = root / config.manual_relative
    excluded_path = root / config.excluded_relative
    manual_entries = parse_manual(_read_utf8(manual_path), output_scopes)
    exclusions = parse_exclusions(_read_utf8(excluded_path))
    for entry in manual_entries:
        if is_excluded(entry.rule, exclusions):
            raise SafetyError(
                f"approved rule is also excluded: {entry.rule.kind},{entry.rule.value}"
            )

    prepared: list[PreparedFile] = []
    readme_values: dict[str, tuple[OutputSpec, Sequence[Rule], str]] = {}
    for spec in config.outputs:
        rules = process_rules(
            entry.rule for entry in manual_entries if entry.scope == spec.scope
        )
        if len(rules) < spec.minimum_rules:
            raise SafetyError(
                f"{spec.name}: {len(rules)} rules is below minimum "
                f"{spec.minimum_rules}"
            )
        output_path = root / spec.relative_path
        old_content = _read_utf8(output_path)
        old_rules = parse_rule_body(old_content, config.policy) if old_content else []
        if old_rules:
            floor = max(spec.minimum_rules, math.ceil(len(old_rules) * 0.60))
            if len(rules) < floor:
                raise SafetyError(
                    f"{spec.name}: proposed count {len(rules)} is below "
                    f"protected floor {floor}"
                )
        new_content, body_changed, updated = render_rule_file(
            spec=spec,
            policy=config.policy,
            rules=rules,
            old_content=old_content,
            now=now,
        )
        old_set = set(old_rules)
        new_set = set(rules)
        prepared.append(
            PreparedFile(
                output_path,
                old_content,
                new_content,
                body_changed,
                added=len(new_set - old_set),
                removed=len(old_set - new_set),
                final_count=len(rules),
            )
        )
        readme_values[spec.scope] = (spec, rules, updated)

    for relative in config.readme_relatives:
        path = root / relative
        old_content = _read_utf8(path)
        if not old_content:
            raise SafetyError(f"README is missing or empty: {path}")
        new_content = update_readme_markers(
            old_content, readme_values, path=path
        )
        prepared.append(
            PreparedFile(path, old_content, new_content, body_changed=False)
        )

    return UpdatePlan(
        upstream_count=len(upstream),
        manual_count=len(manual_entries),
        excluded_count=len(exclusions),
        files=prepared,
    )


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def format_diff(item: PreparedFile, root: Path) -> str:
    relative = str(item.path.relative_to(root)).replace("\\", "/")
    return "".join(
        difflib.unified_diff(
            item.old_content.splitlines(keepends=True),
            item.new_content.splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        )
    )


def build_parser(policy: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Safely update the {policy} Quantumult X rules."
    )
    parser.add_argument("--check", action="store_true", help="check without writing")
    parser.add_argument(
        "--dry-run", action="store_true", help="print diff without writing"
    )
    parser.add_argument("--verbose", action="store_true", help="show source details")
    return parser


def run_update_cli(config: AppConfig, *, root: Path) -> int:
    args = build_parser(config.policy).parse_args()
    if args.check and args.dry_run:
        print("--check and --dry-run cannot be used together", file=sys.stderr)
        return 2
    try:
        plan = prepare_update(config, root=root)
    except RuleError as exc:
        print(f"{config.policy} update failed: {exc}", file=sys.stderr)
        return 2

    if args.verbose:
        for url in config.upstream_urls:
            print(f"Upstream: {url}")
    print(f"Upstream rules: {plan.upstream_count}")
    print(f"Approved manual rules: {plan.manual_count}")
    print(f"Exclusions: {plan.excluded_count}")
    for item in plan.files:
        if item.final_count:
            print(
                f"{item.path.name}: added={item.added} removed={item.removed} "
                f"final={item.final_count} body_changed={'yes' if item.body_changed else 'no'}"
            )
    print(f"Files changed: {sum(item.changed for item in plan.files)}")

    if args.dry_run:
        for item in plan.files:
            if item.changed:
                print(format_diff(item, root), end="")
        return 0
    if args.check:
        return 1 if plan.changed else 0
    if plan.changed:
        for item in plan.files:
            if item.changed:
                atomic_write(item.path, item.new_content)
    return 0


def parse_header(text: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for key in HEADER_KEYS:
        match = re.search(rf"^# {re.escape(key)}:\s*(\d+)\s*$", text, re.MULTILINE)
        if match:
            values[key] = int(match.group(1))
    return values


def validate_candidate_tsv(path: Path, allowed_scopes: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except UnicodeDecodeError as exc:
        return [f"{path}: not UTF-8: {exc}"]
    rows = list(csv.reader(text.splitlines(), delimiter="\t"))
    if not rows or tuple(rows[0]) != CANDIDATE_HEADER:
        return [f"{path}: invalid candidate TSV header"]
    seen: dict[str, int] = {}
    domains: list[str] = []
    for line_number, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if len(row) != len(CANDIDATE_HEADER):
            errors.append(f"{path}:{line_number}: expected eight TSV fields")
            continue
        domain, rule_type, scope, status, source, evidence, risk, _ = row
        try:
            canonical = normalize_domain(domain, allow_single_label=True)
        except SafetyError as exc:
            errors.append(f"{path}:{line_number}: {exc}")
            continue
        if domain != canonical:
            errors.append(f"{path}:{line_number}: domain is not canonical")
        if domain in seen:
            errors.append(
                f"{path}:{line_number}: duplicate of line {seen[domain]}"
            )
        seen[domain] = line_number
        domains.append(domain)
        if rule_type not in {"HOST", "HOST-SUFFIX"}:
            errors.append(f"{path}:{line_number}: invalid rule_type")
        if scope not in allowed_scopes | {
            "ads",
            "ai",
            "historical",
            "shared",
            "telemetry",
            "unknown",
        }:
            errors.append(f"{path}:{line_number}: invalid scope")
        if status not in {
            "confirmed",
            "optional",
            "excluded",
            "historical",
            "needs-review",
        }:
            errors.append(f"{path}:{line_number}: invalid status")
        if risk not in {"low", "medium", "high"}:
            errors.append(f"{path}:{line_number}: invalid risk")
        parsed = urllib.parse.urlsplit(source)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            errors.append(f"{path}:{line_number}: invalid source URL")
        if parsed.query or parsed.fragment:
            errors.append(f"{path}:{line_number}: source URL has query/fragment")
        if not evidence:
            errors.append(f"{path}:{line_number}: evidence is empty")
    if domains != sorted(domains, key=str.casefold):
        errors.append(f"{path}: candidate rows are not sorted by domain")
    return errors


SECRET_PATTERNS = (
    (
        "GitHub token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    ),
    (
        "private key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "UUID-like credential",
        re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
            r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "sensitive URL parameter",
        re.compile(r"(?i)[?&](?:token|password|passwd|api[_-]?key)=[^&#\s]+"),
    ),
    (
        "password assignment",
        re.compile(r"(?i)\b(?:password|passwd)\s*[:=]\s*[\"']?[A-Za-z0-9._~+/\-=]{6,}"),
    ),
)
LOCAL_PATH_PATTERNS = (
    re.compile(r"(?i)\b[A-Z]:\\Users\\"),
    re.compile(r"(?<!\w)/(?:Users|home)/[^/\s]+/"),
)
PRIVACY_PATTERNS = (
    re.compile(
        r"(?:推荐|建议|必须|选择).{0,16}"
        r"(?:台湾|台灣|香港|日本|新加坡|美国|美國).{0,8}(?:节点|節點|代理)"
    ),
    re.compile(r"我的(?:节点|節點|代理|订阅|訂閱|账户|帳戶)"),
    re.compile(r"我(?:使用|会选择|會選擇|已有).{0,16}(?:节点|節點|代理|策略)"),
    re.compile(r"维护者.{0,12}(?:使用|所在|购买|持有)"),
)


def find_sensitive(text: str) -> list[str]:
    findings: list[str] = []
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    for pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            findings.append("local absolute path")
    return findings


def find_privacy_issues(text: str) -> list[str]:
    return [pattern.pattern for pattern in PRIVACY_PATTERNS if pattern.search(text)]


def validate_rule_text(
    text: str,
    *,
    policy: str,
    expected_name: str,
    expected_description: str,
) -> tuple[list[Rule], list[str]]:
    errors: list[str] = []
    if f"# NAME: {expected_name}" not in text:
        errors.append(f"missing NAME header {expected_name!r}")
    if f"# DESCRIPTION: {expected_description}" not in text:
        errors.append("DESCRIPTION header mismatch")
    if f"# AUTHOR: {repository_identity.OWNER}" not in text:
        errors.append("AUTHOR header mismatch")
    if f"# REPO: {repository_identity.REPOSITORY_URL}" not in text:
        errors.append("REPO header mismatch")
    rules: list[Rule] = []
    seen: dict[tuple[str, str], int] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 3:
            errors.append(f"line {line_number}: expected exactly three columns")
            continue
        kind, value, actual_policy = fields
        if actual_policy != policy:
            errors.append(
                f"line {line_number}: policy must be {policy}, got {actual_policy!r}"
            )
        if kind not in TYPE_ORDER:
            errors.append(f"line {line_number}: unsupported type {kind!r}")
            continue
        try:
            rule = make_rule(kind, value)
            validate_rule_allowed(rule)
        except SafetyError as exc:
            errors.append(f"line {line_number}: {exc}")
            continue
        if value != rule.value:
            errors.append(f"line {line_number}: non-canonical value {value!r}")
        key = (rule.kind, rule.value.casefold())
        if key in seen:
            errors.append(f"line {line_number}: duplicate of line {seen[key]}")
        seen[key] = line_number
        rules.append(rule)
    if rules != sorted(rules, key=sort_key):
        errors.append("rules are not sorted")
    if rules != collapse_parent_coverage(rules):
        errors.append("parent HOST-SUFFIX coverage is redundant")
    counts = count_rules(rules)
    header = parse_header(text)
    for key in HEADER_KEYS:
        if key not in header:
            errors.append(f"missing header count {key}")
        elif header[key] != counts[key]:
            errors.append(
                f"header {key}={header[key]} does not match actual {counts[key]}"
            )
    return rules, errors


def validate_markdown_links(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        local = urllib.parse.unquote(target.split("#", 1)[0])
        resolved = (path.parent / local).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{path}: link escapes repository: {target}")
            continue
        if not resolved.exists():
            line_number = text.count("\n", 0, match.start()) + 1
            errors.append(f"{path}:{line_number}: broken link {target!r}")
    return errors


def validate_service(
    config: AppConfig,
    *,
    root: Path,
    extra_checks: Callable[[Mapping[str, Sequence[Rule]], Path], list[str]] | None = None,
) -> tuple[list[str], dict[str, list[Rule]]]:
    errors: list[str] = []
    rules_by_scope: dict[str, list[Rule]] = {}
    required = [
        root / config.manual_relative,
        root / config.excluded_relative,
        root / config.candidates_relative,
        *(root / relative for relative in config.readme_relatives),
        *(root / spec.relative_path for spec in config.outputs),
        root / "rule" / "QuantumultX" / "Bybit" / "Bybit.list",
        root / "rule" / "QuantumultX" / "ClubSim" / "ClubSim.list",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"{path}: required file is missing")

    for spec in config.outputs:
        path = root / spec.relative_path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{path}: not UTF-8: {exc}")
            continue
        rules, file_errors = validate_rule_text(
            text,
            policy=config.policy,
            expected_name=spec.name,
            expected_description=spec.description,
        )
        errors.extend(f"{path}: {error}" for error in file_errors)
        if len(rules) < spec.minimum_rules:
            errors.append(
                f"{path}: only {len(rules)} rules; minimum is {spec.minimum_rules}"
            )
        rules_by_scope[spec.scope] = rules
        updated = extract_updated(text)
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC", updated
        ):
            errors.append(f"{path}: invalid UPDATED timestamp {updated!r}")

    allowed_scopes = {spec.scope for spec in config.outputs}
    candidate_path = root / config.candidates_relative
    if candidate_path.is_file():
        errors.extend(validate_candidate_tsv(candidate_path, allowed_scopes))
    try:
        manual_entries = parse_manual(
            _read_utf8(root / config.manual_relative), allowed_scopes
        )
        exclusions = parse_exclusions(_read_utf8(root / config.excluded_relative))
        approved_by_scope = {
            scope: process_rules(
                entry.rule for entry in manual_entries if entry.scope == scope
            )
            for scope in allowed_scopes
        }
        for scope, approved in approved_by_scope.items():
            if rules_by_scope.get(scope) != approved:
                errors.append(
                    f"{config.policy} {scope}: formal rules do not match approved manual data"
                )
        for entry in manual_entries:
            if is_excluded(entry.rule, exclusions):
                errors.append(
                    f"approved rule is excluded: {entry.rule.kind},{entry.rule.value}"
                )
    except RuleError as exc:
        errors.append(f"approved data: {exc}")

    for relative in config.readme_relatives:
        path = root / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for spec in config.outputs:
            rules = rules_by_scope.get(spec.scope, [])
            count_marker = (
                f"<!-- {spec.count_marker}_START -->{_count_text(rules)}"
                f"<!-- {spec.count_marker}_END -->"
            )
            if count_marker not in text:
                errors.append(f"{path}: count marker mismatch for {spec.name}")
            rule_text = (root / spec.relative_path).read_text(encoding="utf-8")
            updated = extract_updated(rule_text)
            updated_marker = (
                f"<!-- {spec.updated_marker}_START -->{updated}"
                f"<!-- {spec.updated_marker}_END -->"
            )
            if updated_marker not in text:
                errors.append(f"{path}: update marker mismatch for {spec.name}")
            raw_url = (
                f"{repository_identity.RAW_BASE_URL}/{spec.relative_path}"
            )
            if raw_url not in text:
                errors.append(f"{path}: missing real Raw URL {raw_url}")
        errors.extend(validate_markdown_links(path, root))
        for issue in find_privacy_issues(text):
            errors.append(f"{path}: region-specific or personal wording: {issue}")

    public_suffixes = {".md", ".list", ".txt", ".tsv", ".py", ".yml", ".yaml"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in public_suffixes:
            continue
        if any(part in {".git", ".codex-tools", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for finding in find_sensitive(text):
            errors.append(f"{path}: contains possible {finding}")

    if extra_checks:
        errors.extend(extra_checks(rules_by_scope, root))
    return errors, rules_by_scope
