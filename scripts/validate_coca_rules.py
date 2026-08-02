#!/usr/bin/env python3
"""Validate COCA rules, reviewed data, documentation, and product isolation."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence

import quantumultx_rule_utils as utils
import update_coca_quantumultx as updater


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MAIN = [
    utils.Rule("HOST", "wwallet.app.link"),
    utils.Rule("HOST-SUFFIX", "coca.xyz"),
]
COCA_PUBLIC_PATHS = (
    ROOT / "README.md",
    ROOT / updater.CONFIG.manual_relative,
    ROOT / updater.CONFIG.excluded_relative,
    ROOT / updater.CONFIG.candidates_relative,
    ROOT / "rule/QuantumultX/COCA/COCA.list",
    ROOT / "rule/QuantumultX/COCA/README.md",
    ROOT / "scripts/update_coca_quantumultx.py",
    ROOT / "scripts/validate_coca_rules.py",
    ROOT / "tests/test_coca_rules.py",
    ROOT / "tests/test_root_readme_app_order.py",
    ROOT / ".github/workflows/update-coca-quantumultx.yml",
)
EMAIL_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])"
)
ALLOWED_PUBLIC_EMAILS = frozenset(
    {"41898282+github-actions[bot]@users.noreply.github.com"}
)
PLACEHOLDER_TOKENS = (
    "<" + "OWNER" + ">",
    "<" + "REPOSITORY" + ">",
    "<" + "BRANCH" + ">",
    "<" + "USERNAME" + ">",
    "YOUR_" + "USERNAME",
    "YOUR_" + "REPOSITORY",
    "TO" + "DO",
)


def _other_rule_diff(root: Path) -> list[str]:
    """Report uncommitted rule-tree changes outside the COCA directory."""

    safe_root = root.resolve().as_posix()
    commands = (
        [
            "git",
            "-c",
            f"safe.directory={safe_root}",
            "diff",
            "--name-only",
            "HEAD",
            "--",
            "rule/QuantumultX",
        ],
        [
            "git",
            "-c",
            f"safe.directory={safe_root}",
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            "rule/QuantumultX",
        ],
    )
    changed: set[str] = set()
    for command in commands:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            return [f"unable to verify other rule changes: {result.stderr.strip()}"]
        changed.update(
            line.strip().replace("\\", "/")
            for line in result.stdout.splitlines()
        )
    return sorted(
        path
        for path in changed
        if path and not path.startswith("rule/QuantumultX/COCA/")
    )


def _matches_root(domain: str, root: str) -> bool:
    return domain == root or domain.endswith(f".{root}")


def extra_checks(
    rules_by_scope: Mapping[str, Sequence[utils.Rule]], root: Path
) -> list[str]:
    errors: list[str] = []
    main = list(rules_by_scope.get("coca-core", ()))
    if main != EXPECTED_MAIN:
        errors.append(
            "COCA main rules must contain only the approved first-party root "
            "and exact app-specific Branch tenant"
        )
    if any(rule.kind in {"IP-CIDR", "IP6-CIDR"} for rule in main):
        errors.append("COCA must not contain public IP ranges")

    list_path = root / updater.CONFIG.outputs[0].relative_path
    if list_path.is_file():
        list_text = list_path.read_text(encoding="utf-8")
        expected_source = (
            "# SOURCE: COCA official sources and reviewed public upstreams"
        )
        if expected_source not in list_text:
            errors.append(f"{list_path}: SOURCE header mismatch")

    for name in ("COCA-Web3.list", "COCA-Regional.list"):
        if (root / "rule" / "QuantumultX" / "COCA" / name).exists():
            errors.append(f"unsubstantiated optional output exists: {name}")

    prohibited_roots = {
        "app.link",
        "coca-cola.com",
        "coca-colacompany.com",
        "coca.com",
        "freshdesk.com",
        "mastercard.com",
        "privy.io",
        "statuspage.io",
        "sumsub.com",
        "visa.com",
        "walletconnect.com",
        "walletconnect.org",
        "wirexapp.com",
    }
    for rule in main:
        for prohibited in prohibited_roots:
            if rule.kind == "HOST-SUFFIX" and _matches_root(
                rule.value, prohibited
            ):
                errors.append(
                    f"COCA main contains prohibited shared or unrelated root: "
                    f"{rule.value}"
                )
            if rule.kind == "HOST" and rule.value == prohibited:
                errors.append(
                    f"COCA main contains prohibited shared or unrelated host: "
                    f"{rule.value}"
                )
    if any("coca-cola" in rule.value or rule.value == "coca.com" for rule in main):
        errors.append("Coca-Cola or unrelated homonym entered the COCA rule")
    if any(
        rule.value.endswith("wirexapp.com")
        or rule.value == "wirex.app.link"
        or rule.value == "wirexone.freshdesk.com"
        for rule in main
    ):
        errors.append("Wirex shared, Classic Wirex, or Wirex One host entered COCA")

    exclusions = utils.parse_exclusions(
        (root / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
    )
    required_exclusions = {
        "amazonaws.com",
        "app.link",
        "apple.com",
        "cloudflare.net",
        "cloudfront.net",
        "coca-cola.com",
        "coca-colacompany.com",
        "coca.com",
        "freshdesk.com",
        "mastercard.com",
        "privy.io",
        "sentry.io",
        "spatium.net",
        "statuspage.io",
        "sumsub.com",
        "visa.com",
        "walletconnect.com",
        "walletconnect.org",
        "wirex.app.link",
        "wirexapp.com",
        "wirexone.freshdesk.com",
        "wixstatic.com",
    }
    missing_exclusions = sorted(required_exclusions - exclusions.keys())
    if missing_exclusions:
        errors.append(
            "COCA exclusion list is missing: " + ", ".join(missing_exclusions)
        )

    candidates = (root / updater.CONFIG.candidates_relative).read_text(
        encoding="utf-8"
    )
    required_rows = (
        "api-baas.wirexapp.com\tHOST\twirex-shared\tneeds-review\t",
        "coca-cola.com\tHOST-SUFFIX\tunknown\texcluded\t",
        "coca.com\tHOST-SUFFIX\tunknown\texcluded\t",
        "coca.xyz\tHOST-SUFFIX\tcoca-core\tconfirmed\t",
        "mastercard.com\tHOST-SUFFIX\tcard\texcluded\t",
        "privy.io\tHOST-SUFFIX\tauthentication\texcluded\t",
        "sumsub.com\tHOST-SUFFIX\tauthentication\texcluded\t",
        "walletconnect.com\tHOST-SUFFIX\twalletconnect\texcluded\t",
        "wirex.app.link\tHOST\tclassic-wirex\texcluded\t",
        "wirexapp.com\tHOST-SUFFIX\twirex-shared\tconfirmed\t",
        "wirexone.freshdesk.com\tHOST\twirexone\texcluded\t",
        "wwallet.app.link\tHOST\tcoca-core\tconfirmed\t",
    )
    for row_start in required_rows:
        if row_start not in candidates:
            errors.append(f"COCA candidate classification is missing: {row_start}")

    for path in COCA_PUBLIC_PATHS:
        if not path.is_file():
            errors.append(f"{path}: required COCA project file is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?i)\b(?:vless|vmess|trojan|ss)://", text):
            errors.append(f"{path}: contains a private subscription scheme")
        for placeholder in PLACEHOLDER_TOKENS:
            if placeholder in text:
                errors.append(f"{path}: contains placeholder {placeholder!r}")
        for issue in utils.find_privacy_issues(text):
            errors.append(
                f"{path}: contains personal or region-specific wording: {issue}"
            )
        unexpected_emails = sorted(
            {
                match.group(0)
                for match in EMAIL_RE.finditer(text)
                if match.group(0).casefold()
                not in {value.casefold() for value in ALLOWED_PUBLIC_EMAILS}
            }
        )
        if unexpected_emails:
            errors.append(
                f"{path}: contains an unexpected email address: "
                + ", ".join(unexpected_emails)
            )

    detail = root / "rule/QuantumultX/COCA/README.md"
    if detail.is_file():
        detail_text = detail.read_text(encoding="utf-8")
        required_statements = (
            "Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程或 Bundle ID 匹配。",
            "如果其他 App 访问相同域名，也可能命中 COCA 规则。",
            "如果 COCA 使用尚未收录的新域名，请求可能进入其他策略。",
            "本项目刻意避免收录公共 CDN、共享身份平台、KYC 平台、卡组织、银行、Wirex 共享后端、Privy、WalletConnect、公共 RPC、广告、统计和系统推送根域名。",
            "本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料。",
            "本项目不预设、记录或推荐用户使用的节点国家、代理服务商或订阅来源。",
            "规则只改变请求的网络出口，不改变账户身份、居住地、服务资格、KYC 状态、钱包控制权、卡片资格或监管要求。",
            "根据自身网络环境和服务可用性，将该远程资源绑定到适当的现有策略组。",
        )
        for statement in required_statements:
            if statement not in detail_text:
                errors.append(f"{detail}: missing required statement: {statement}")

    other_changes = _other_rule_diff(root)
    if other_changes:
        errors.append(
            "existing application rule files have uncommitted changes: "
            + ", ".join(other_changes)
        )
    return errors


def main() -> int:
    errors, rules = utils.validate_service(
        updater.CONFIG,
        root=ROOT,
        extra_checks=extra_checks,
    )
    if errors:
        print("COCA validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    counts = utils.count_rules(rules["coca-core"])
    print(
        "COCA validation passed: "
        f"{counts['TOTAL']} main rules "
        f"(HOST={counts['HOST']}, HOST-SUFFIX={counts['HOST-SUFFIX']}, "
        f"IP-CIDR={counts['IP-CIDR']}, IP6-CIDR={counts['IP6-CIDR']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
