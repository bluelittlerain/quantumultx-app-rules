#!/usr/bin/env python3
"""Validate ClubSim rules, documentation, privacy, and repository metadata."""

from __future__ import annotations

import csv
import ipaddress
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Iterable, Sequence

import repository_identity
import update_clubsim_quantumultx as updater


ROOT = Path(__file__).resolve().parents[1]
MAIN_RULE = ROOT / "rule" / "QuantumultX" / "ClubSim" / "ClubSim.list"
NETWORK_RULE = (
    ROOT / "rule" / "QuantumultX" / "ClubSim" / "ClubSim-Network.list"
)
DETAIL_README = ROOT / "rule" / "QuantumultX" / "ClubSim" / "README.md"
ROOT_README = ROOT / "README.md"
CANDIDATES = ROOT / "data" / "clubsim_candidates.tsv"
MANUAL = ROOT / "data" / "clubsim_manual_domains.txt"
NETWORK_DATA = ROOT / "data" / "clubsim_network_domains.txt"
EXCLUDED = ROOT / "data" / "clubsim_excluded_domains.txt"

EXPECTED_REPO_URL = repository_identity.REPOSITORY_URL
RAW_BASE = (
    f"{repository_identity.RAW_BASE_URL}/rule/QuantumultX/ClubSim"
)
EXPECTED_BYBIT_LINKS = (
    f"{repository_identity.RAW_BASE_URL}/rule/QuantumultX/Bybit/Bybit.list",
    f"{repository_identity.RAW_BASE_URL}"
    "/rule/QuantumultX/Bybit/Bybit-Regional.list",
)

ALLOWED_TYPES = frozenset(updater.TYPE_ORDER)
HEADER_KEYS = ("HOST", "HOST-SUFFIX", "IP-CIDR", "IP6-CIDR", "TOTAL")
REQUIRED_FILES = (
    MAIN_RULE,
    NETWORK_RULE,
    DETAIL_README,
    ROOT_README,
    MANUAL,
    NETWORK_DATA,
    EXCLUDED,
    CANDIDATES,
    ROOT / "scripts" / "discover_clubsim_domains.py",
    ROOT / "scripts" / "update_clubsim_quantumultx.py",
    ROOT / "scripts" / "validate_clubsim_rules.py",
    ROOT / "scripts" / "repository_identity.py",
    ROOT / "tests" / "test_clubsim_rules.py",
    ROOT / ".github" / "workflows" / "update-clubsim-quantumultx.yml",
)
PUBLIC_TEXT_FILES = REQUIRED_FILES

PLACEHOLDER_PATTERNS = (
    re.compile(r"<(?:OWNER|USERNAME|REPOSITORY|BRANCH)>", re.IGNORECASE),
    re.compile(r"\bYOUR[_ -]?(?:USERNAME|REPOSITORY)\b", re.IGNORECASE),
    re.compile(r"\bYYYY-MM-DD\b"),
    re.compile(r"https?://(?:www\.)?example\.(?:com|org)", re.IGNORECASE),
)
SECRET_PATTERNS = (
    (
        "GitHub token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    ),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
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
        "sensitive assignment",
        re.compile(
            r"(?i)\b(?:token|password|passwd|cookie|api[_ -]?key)"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9._~+/\-=]{6,}"
        ),
    ),
    (
        "sensitive URL parameter",
        re.compile(r"(?i)[?&](?:token|password|passwd|api[_-]?key)=[^&#\s]+"),
    ),
)
LOCAL_PATH_PATTERNS = (
    re.compile(r"(?i)\b[A-Z]:\\Users\\"),
    re.compile(r"(?<!\w)/(?:Users|home)/[^/\s]+/"),
)
FIRST_PERSON_PATTERNS = (
    re.compile(r"维护者.{0,12}(?:使用|所在|购买)"),
    re.compile(r"我的(?:节点|代理|订阅|网络环境|账户)"),
    re.compile(r"我(?:已经|已有|会选择|使用).{0,16}(?:节点|代理|策略)"),
    re.compile(r"(?i)\bI use (?:a |my )?(?:node|proxy|provider)"),
)
RECOMMENDATION_PATTERNS = (
    re.compile(r"(?:建议|必须|推荐|选择).{0,14}(?:国家|地区).{0,8}(?:节点|代理)"),
    re.compile(r"(?:建议|必须|推荐).{0,14}(?:节点|代理出口)"),
    re.compile(
        r"(?i)\b(?:recommend|must use|choose).{0,30}"
        r"(?:country|regional?) (?:node|proxy)"
    ),
)
DISCLAIMER_MARKERS = ("不预设", "不收集", "不记录", "不推荐", "不得")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def decode_utf8(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"{relative(path)}: file does not exist")
        return ""
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{relative(path)}: not valid UTF-8: {exc}")
        return ""


def parse_header(text: str, path: Path, errors: list[str]) -> dict[str, int]:
    values: dict[str, int] = {}
    for key in HEADER_KEYS:
        match = re.search(rf"^# {re.escape(key)}:\s*(\d+)\s*$", text, re.MULTILINE)
        if not match:
            errors.append(f"{relative(path)}: missing header count {key}")
        else:
            values[key] = int(match.group(1))
    return values


def validate_rule_file(
    path: Path,
    *,
    minimum_rules: int,
    network_file: bool,
) -> tuple[list[updater.Rule], str, list[str]]:
    errors: list[str] = []
    text = decode_utf8(path, errors)
    if not text:
        return [], text, errors

    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            errors.append(
                f"{relative(path)}: contains placeholder matching {pattern.pattern!r}"
            )
    if f"# REPO: {EXPECTED_REPO_URL}" not in text:
        errors.append(f"{relative(path)}: repository header is not the real repository")

    rules: list[updater.Rule] = []
    seen: dict[tuple[str, str], int] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 3:
            errors.append(
                f"{relative(path)}:{line_number}: expected exactly three columns"
            )
            continue
        kind, value, policy = parts
        if policy != "ClubSim":
            errors.append(
                f"{relative(path)}:{line_number}: policy must be ClubSim, got {policy!r}"
            )
        if kind not in ALLOWED_TYPES:
            errors.append(
                f"{relative(path)}:{line_number}: unsupported type {kind!r}"
            )
            continue
        if re.match(
            r"^(?:DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|HOST-KEYWORD|"
            r"PROCESS-NAME|PROCESS-PATH|USER-AGENT|RULE-SET|SCRIPT)$",
            kind,
            re.IGNORECASE,
        ):
            errors.append(f"{relative(path)}:{line_number}: forbidden type {kind!r}")
            continue
        try:
            rule = updater.make_rule(kind, value)
            updater.validate_rule_allowed(rule)
        except updater.SafetyError as exc:
            errors.append(f"{relative(path)}:{line_number}: {exc}")
            continue
        if value != rule.value:
            errors.append(
                f"{relative(path)}:{line_number}: non-canonical value {value!r}; "
                f"expected {rule.value!r}"
            )
        key = (rule.kind, rule.value.casefold())
        if key in seen:
            errors.append(
                f"{relative(path)}:{line_number}: duplicate of line {seen[key]}"
            )
        else:
            seen[key] = line_number
        if network_file:
            if rule.value not in updater.NETWORK_DOMAINS:
                errors.append(
                    f"{relative(path)}:{line_number}: unapproved network domain"
                )
        elif rule.value in updater.NETWORK_DOMAINS or "epdg." in rule.value:
            errors.append(
                f"{relative(path)}:{line_number}: network domain is in the main App rules"
            )
        rules.append(rule)

    if len(rules) < minimum_rules:
        errors.append(
            f"{relative(path)}: only {len(rules)} rules; minimum is {minimum_rules}"
        )
    if rules != updater.sort_rules(rules):
        errors.append(f"{relative(path)}: rules are not in canonical order")
    if rules != updater.collapse_parent_coverage(rules):
        errors.append(f"{relative(path)}: parent HOST-SUFFIX coverage is redundant")

    counts = updater.count_rules(rules)
    header = parse_header(text, path, errors)
    for key in HEADER_KEYS:
        if key in header and header[key] != counts[key]:
            errors.append(
                f"{relative(path)}: header {key}={header[key]}, actual={counts[key]}"
            )
    return rules, text, errors


def _extract_updated(text: str, path: Path, errors: list[str]) -> str:
    value = updater.extract_updated_at(text)
    if not value:
        errors.append(f"{relative(path)}: missing UPDATED header")
        return ""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC", value):
        errors.append(f"{relative(path)}: invalid UPDATED timestamp {value!r}")
    return value


def _marker_counts(
    text: str, prefix: str, path: Path, errors: list[str]
) -> dict[str, int] | None:
    pattern = re.compile(
        rf"<!-- {prefix}_COUNTS_START -->(\d+) 条"
        rf"（HOST (\d+)，HOST-SUFFIX (\d+)，"
        rf"IP-CIDR (\d+)，IP6-CIDR (\d+)）"
        rf"<!-- {prefix}_COUNTS_END -->"
    )
    match = pattern.search(text)
    if not match:
        errors.append(f"{relative(path)}: missing {prefix} count marker")
        return None
    total, host, suffix, ipv4, ipv6 = map(int, match.groups())
    return {
        "TOTAL": total,
        "HOST": host,
        "HOST-SUFFIX": suffix,
        "IP-CIDR": ipv4,
        "IP6-CIDR": ipv6,
    }


def validate_readme_metadata(
    path: Path,
    *,
    main_rules: Sequence[updater.Rule],
    network_rules: Sequence[updater.Rule],
    main_updated: str,
    network_updated: str,
) -> list[str]:
    errors: list[str] = []
    text = decode_utf8(path, errors)
    if not text:
        return errors
    expected = {
        "CLUBSIM_MAIN": updater.count_rules(main_rules),
        "CLUBSIM_NETWORK": updater.count_rules(network_rules),
    }
    for prefix, counts in expected.items():
        actual = _marker_counts(text, prefix, path, errors)
        if actual is not None and actual != counts:
            errors.append(
                f"{relative(path)}: {prefix} README counts {actual} "
                f"do not match {counts}"
            )
    if path == DETAIL_README:
        for prefix, value in (
            ("CLUBSIM_MAIN", main_updated),
            ("CLUBSIM_NETWORK", network_updated),
        ):
            match = re.search(
                rf"<!-- {prefix}_UPDATED_START -->(.*?)"
                rf"<!-- {prefix}_UPDATED_END -->",
                text,
            )
            if not match:
                errors.append(f"{relative(path)}: missing {prefix} update marker")
            elif match.group(1) != value:
                errors.append(
                    f"{relative(path)}: {prefix} update time "
                    f"{match.group(1)!r} does not match {value!r}"
                )
    return errors


def find_sensitive(text: str) -> list[str]:
    findings: list[str] = []
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    for pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            findings.append("local absolute path")
    return findings


def validate_public_privacy(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in FIRST_PERSON_PATTERNS:
            if pattern.search(line):
                errors.append(
                    f"{relative(path)}:{line_number}: personal maintainer configuration"
                )
        if any(marker in line for marker in DISCLAIMER_MARKERS):
            continue
        for pattern in RECOMMENDATION_PATTERNS:
            if pattern.search(line):
                errors.append(
                    f"{relative(path)}:{line_number}: region-specific proxy recommendation"
                )
    return errors


def validate_no_secrets_or_private_paths() -> list[str]:
    errors: list[str] = []
    for path in PUBLIC_TEXT_FILES:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for finding in find_sensitive(text):
            errors.append(f"{relative(path)}: contains possible {finding}")
        if path.suffix in {".md", ".list", ".txt", ".tsv", ".yml", ".yaml"}:
            errors.extend(validate_public_privacy(path, text))
    return errors


def validate_candidates() -> list[str]:
    errors: list[str] = []
    text = decode_utf8(CANDIDATES, errors)
    if not text:
        return errors
    expected_header = [
        "domain",
        "rule_type",
        "scope",
        "status",
        "source",
        "evidence",
        "risk",
        "notes",
    ]
    rows = list(csv.reader(text.splitlines(), delimiter="\t"))
    if not rows or rows[0] != expected_header:
        errors.append(f"{relative(CANDIDATES)}: invalid TSV header")
        return errors
    seen: dict[str, int] = {}
    for line_number, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if len(row) != len(expected_header):
            errors.append(
                f"{relative(CANDIDATES)}:{line_number}: expected eight fields"
            )
            continue
        domain, rule_type, scope, status, source, evidence, risk, _ = row
        try:
            canonical = updater.normalize_domain(domain)
        except updater.SafetyError as exc:
            errors.append(f"{relative(CANDIDATES)}:{line_number}: {exc}")
            continue
        if domain != canonical:
            errors.append(
                f"{relative(CANDIDATES)}:{line_number}: domain is not lowercase/canonical"
            )
        if domain in seen:
            errors.append(
                f"{relative(CANDIDATES)}:{line_number}: duplicate of line {seen[domain]}"
            )
        seen[domain] = line_number
        if rule_type not in {"HOST", "HOST-SUFFIX"}:
            errors.append(
                f"{relative(CANDIDATES)}:{line_number}: invalid rule_type"
            )
        if scope not in {"prepaid-app", "monthly-app", "network", "shared", "unknown"}:
            errors.append(f"{relative(CANDIDATES)}:{line_number}: invalid scope")
        if status not in {"confirmed", "optional", "excluded", "needs-review"}:
            errors.append(f"{relative(CANDIDATES)}:{line_number}: invalid status")
        if risk not in {"low", "medium", "high"}:
            errors.append(f"{relative(CANDIDATES)}:{line_number}: invalid risk")
        parsed = urllib.parse.urlsplit(source)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            errors.append(f"{relative(CANDIDATES)}:{line_number}: invalid source URL")
        if parsed.query or parsed.fragment:
            errors.append(
                f"{relative(CANDIDATES)}:{line_number}: source URL has query/fragment"
            )
        if not evidence:
            errors.append(
                f"{relative(CANDIDATES)}:{line_number}: evidence is empty"
            )
    domains = [row[0] for row in rows[1:] if row]
    if domains != sorted(domains, key=str.casefold):
        errors.append(f"{relative(CANDIDATES)}: rows are not sorted by domain")
    return errors


def validate_markdown_links(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        local_target = urllib.parse.unquote(target.split("#", 1)[0])
        resolved = (path.parent / local_target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{relative(path)}: link escapes repository: {target}")
            continue
        if not resolved.exists():
            line_number = text.count("\n", 0, match.start()) + 1
            errors.append(
                f"{relative(path)}:{line_number}: broken local link {target!r}"
            )
    return errors


def validate_repository_links() -> list[str]:
    errors: list[str] = []
    root_text = ROOT_README.read_text(encoding="utf-8")
    detail_text = DETAIL_README.read_text(encoding="utf-8")
    for link in EXPECTED_BYBIT_LINKS:
        if link not in root_text:
            errors.append(f"{relative(ROOT_README)}: existing Bybit link was broken")
    expected_main = f"{RAW_BASE}/ClubSim.list"
    expected_network = f"{RAW_BASE}/ClubSim-Network.list"
    for link in (expected_main, expected_network):
        if link not in root_text or link not in detail_text:
            errors.append(f"README files are missing real Raw link: {link}")
    if (ROOT / "rule" / "QuantumultX" / "ClubSim" / "ClubSim-Monthly.list").exists():
        errors.append(
            "ClubSim-Monthly.list exists without independently validated monthly domains"
        )
    return errors


def validate_approved_separation(
    main_rules: Sequence[updater.Rule],
    network_rules: Sequence[updater.Rule],
) -> list[str]:
    errors: list[str] = []
    manual_text = MANUAL.read_text(encoding="utf-8")
    network_text = NETWORK_DATA.read_text(encoding="utf-8")
    try:
        approved_main = updater.parse_approved_data(manual_text, "prepaid-app")
        approved_network = updater.parse_approved_data(network_text, "network")
    except updater.SafetyError as exc:
        return [f"approved data: {exc}"]
    if list(main_rules) != approved_main:
        errors.append("ClubSim.list does not exactly match approved prepaid-app data")
    if list(network_rules) != approved_network:
        errors.append("ClubSim-Network.list does not exactly match approved network data")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.is_file():
            errors.append(f"{relative(path)}: required file is missing")

    main_rules, main_text, main_errors = validate_rule_file(
        MAIN_RULE, minimum_rules=1, network_file=False
    )
    errors.extend(main_errors)
    network_rules, network_text, network_errors = validate_rule_file(
        NETWORK_RULE, minimum_rules=5, network_file=True
    )
    errors.extend(network_errors)

    main_updated = _extract_updated(main_text, MAIN_RULE, errors) if main_text else ""
    network_updated = (
        _extract_updated(network_text, NETWORK_RULE, errors) if network_text else ""
    )
    if main_rules and network_rules:
        errors.extend(
            validate_approved_separation(main_rules, network_rules)
        )
        for readme in (ROOT_README, DETAIL_README):
            errors.extend(
                validate_readme_metadata(
                    readme,
                    main_rules=main_rules,
                    network_rules=network_rules,
                    main_updated=main_updated,
                    network_updated=network_updated,
                )
            )

    errors.extend(validate_candidates())
    errors.extend(validate_no_secrets_or_private_paths())
    if ROOT_README.is_file():
        errors.extend(validate_markdown_links(ROOT_README))
    if DETAIL_README.is_file():
        errors.extend(validate_markdown_links(DETAIL_README))
    if ROOT_README.is_file() and DETAIL_README.is_file():
        errors.extend(validate_repository_links())

    if errors:
        print("ClubSim validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    total = len(main_rules) + len(network_rules)
    print(
        "ClubSim validation passed: "
        f"{len(main_rules)} main rules, {len(network_rules)} network rules, "
        f"{total} total."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
