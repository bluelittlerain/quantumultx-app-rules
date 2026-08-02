#!/usr/bin/env python3
"""Validate Wirex One rules, reviewed data, documentation, and isolation."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence

import quantumultx_rule_utils as utils
import update_wirexone_quantumultx as updater


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MAIN = [
    utils.Rule("HOST", "wirexone.freshdesk.com"),
    utils.Rule("HOST-SUFFIX", "wirexapp.com"),
]
WIREX_PUBLIC_PATHS = (
    ROOT / "README.md",
    ROOT / updater.CONFIG.manual_relative,
    ROOT / updater.CONFIG.excluded_relative,
    ROOT / updater.CONFIG.candidates_relative,
    ROOT / "rule/QuantumultX/WirexOne/WirexOne.list",
    ROOT / "rule/QuantumultX/WirexOne/README.md",
    ROOT / "scripts/update_wirexone_quantumultx.py",
    ROOT / "scripts/validate_wirexone_rules.py",
    ROOT / "tests/test_wirexone_rules.py",
    ROOT / "tests/test_root_readme_app_order.py",
    ROOT / ".github/workflows/update-wirexone-quantumultx.yml",
)


def _other_rule_diff(root: Path) -> list[str]:
    """Report uncommitted rule-tree changes outside the Wirex One directory."""

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
        changed.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines())
    return sorted(
        path
        for path in changed
        if path and not path.startswith("rule/QuantumultX/WirexOne/")
    )


def extra_checks(
    rules_by_scope: Mapping[str, Sequence[utils.Rule]], root: Path
) -> list[str]:
    errors: list[str] = []
    main = list(rules_by_scope.get("wirexone-core", ()))
    if main != EXPECTED_MAIN:
        errors.append(
            "WirexOne main rules must contain only the approved first-party root "
            "and dedicated help tenant"
        )
    if any(rule.kind in {"IP-CIDR", "IP6-CIDR"} for rule in main):
        errors.append("WirexOne must not contain public IP ranges")

    list_path = root / updater.CONFIG.outputs[0].relative_path
    if list_path.is_file():
        list_text = list_path.read_text(encoding="utf-8")
        expected_source = (
            "# SOURCE: Wirex One official sources and reviewed public upstreams"
        )
        if expected_source not in list_text:
            errors.append(f"{list_path}: SOURCE header mismatch")

    for name in ("WirexOne-Web3.list", "WirexOne-Regional.list"):
        if (root / "rule" / "QuantumultX" / "WirexOne" / name).exists():
            errors.append(f"unsubstantiated optional output exists: {name}")

    exclusions = utils.parse_exclusions(
        (root / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
    )
    required_exclusions = {
        "amazonaws.com",
        "app.link",
        "apple.com",
        "arc.network",
        "cloudflare.net",
        "cloudfront.net",
        "freshdesk.com",
        "mastercard.com",
        "paypal.com",
        "privy.io",
        "sentry.io",
        "stripe.com",
        "sumsub.com",
        "visa.com",
        "walletconnect.com",
        "wirex.app.link",
        "wirex.com",
        "wirexapp.tech",
        "wirexpaychain.com",
    }
    missing_exclusions = sorted(required_exclusions - exclusions.keys())
    if missing_exclusions:
        errors.append(
            "WirexOne exclusion list is missing: " + ", ".join(missing_exclusions)
        )

    candidates = (root / updater.CONFIG.candidates_relative).read_text(
        encoding="utf-8"
    )
    required_rows = (
        "api-baas.wirexapp.com\tHOST\twirex-shared-core\tconfirmed\t",
        "privy.io\tHOST-SUFFIX\tidentity\texcluded\t",
        "sumsub.com\tHOST-SUFFIX\tidentity\texcluded\t",
        "wirex.app.link\tHOST\tclassic-wirex\tneeds-review\t",
        "wirex.com\tHOST-SUFFIX\tunknown\texcluded\t",
        "wirexapp.com\tHOST-SUFFIX\twirex-shared-core\tconfirmed\t",
        "wirexone.freshdesk.com\tHOST\tsupport\tconfirmed\t",
        "wirexpaychain.com\tHOST-SUFFIX\tblockchain\tneeds-review\t",
    )
    for row_start in required_rows:
        if row_start not in candidates:
            errors.append(f"WirexOne candidate classification is missing: {row_start}")

    for path in WIREX_PUBLIC_PATHS:
        if not path.is_file():
            errors.append(f"{path}: required Wirex One project file is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?i)\b(?:vless|vmess|trojan|ss)://", text):
            errors.append(f"{path}: contains a private subscription scheme")
        for issue in utils.find_privacy_issues(text):
            errors.append(
                f"{path}: contains personal or region-specific wording: {issue}"
            )

    detail = root / "rule/QuantumultX/WirexOne/README.md"
    if detail.is_file():
        detail_text = detail.read_text(encoding="utf-8")
        required_statements = (
            "Quantumult X 常规分流按照请求的目标域名和 IP 匹配，并不是真正按照 iOS App 进程或 Bundle ID 匹配。",
            "如果其他 App 访问相同域名，也可能命中 Wirex One 规则。",
            "如果 Wirex One 使用尚未收录的新域名，请求可能进入其他策略。",
            "本项目刻意避免收录公共 CDN、共享身份平台、KYC 平台、卡组织、银行、公共 RPC、广告、统计和系统推送根域名。",
            "本项目不收集、记录或推荐用户使用的节点国家、代理服务商、订阅地址或账户资料。",
            "规则只改变请求的网络出口，不改变账户身份、居住地、服务资格、KYC 状态、银行卡资格或监管要求。",
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
        print("Wirex One validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    counts = utils.count_rules(rules["wirexone-core"])
    print(
        "Wirex One validation passed: "
        f"{counts['TOTAL']} main rules "
        f"(HOST={counts['HOST']}, HOST-SUFFIX={counts['HOST-SUFFIX']}, "
        f"IP-CIDR={counts['IP-CIDR']}, IP6-CIDR={counts['IP6-CIDR']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
