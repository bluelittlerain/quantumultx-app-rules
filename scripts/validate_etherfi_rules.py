#!/usr/bin/env python3
"""Validate Ether.fi Quantumult X rules and public project documentation."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

import quantumultx_rule_utils as utils
import update_etherfi_quantumultx as updater


ROOT = Path(__file__).resolve().parents[1]


def extra_checks(
    rules_by_scope: Mapping[str, Sequence[utils.Rule]], root: Path
) -> list[str]:
    errors: list[str] = []
    main = list(rules_by_scope.get("main", ()))
    expected = [utils.Rule("HOST-SUFFIX", "ether.fi")]
    if main != expected:
        errors.append("EtherFi main rules must contain only the approved ether.fi root")

    exclusions = utils.parse_exclusions(
        (root / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
    )
    required_exclusions = {
        "amazonaws.com",
        "apple.com",
        "cloudflare.com",
        "cloudfront.net",
        "etherfi.gitbook.io",
        "etherfi.onelink.me",
        "ethereum.org",
        "googleapis.com",
        "onelink.me",
        "reown.com",
        "safe.global",
        "sentry.io",
        "turnkey.com",
        "walletconnect.com",
        "walletconnect.org",
    }
    missing_exclusions = sorted(required_exclusions - exclusions.keys())
    if missing_exclusions:
        errors.append(
            "EtherFi exclusion list is missing: " + ", ".join(missing_exclusions)
        )

    candidate_text = (
        root / updater.CONFIG.candidates_relative
    ).read_text(encoding="utf-8")
    required_candidate_rows = (
        "ether.fi\tHOST-SUFFIX\tmain\tconfirmed\t",
        "etherfi.gitbook.io\tHOST\tshared\texcluded\t",
        "etherfi.onelink.me\tHOST\tshared\texcluded\t",
        "walletconnect.org\tHOST-SUFFIX\tshared\texcluded\t",
    )
    for row_start in required_candidate_rows:
        if row_start not in candidate_text:
            errors.append(f"EtherFi candidate classification is missing: {row_start}")

    web3_path = root / "rule/QuantumultX/EtherFi/EtherFi-Web3.list"
    if web3_path.exists():
        errors.append(
            "EtherFi-Web3.list exists without an approved independent first-party root"
        )

    root_readme = (root / "README.md").read_text(encoding="utf-8")
    for heading in (
        "## Available Rules",
        "## Usage",
        "## Scope and Limitations",
        "## Privacy",
        "## License",
    ):
        if heading not in root_readme:
            errors.append(f"root README is missing section {heading}")
    if "同一个 GitHub 仓库不代表不同 App 的规则被合并" not in root_readme:
        errors.append("root README does not explain independent rule resources")

    etherfi_public_paths = (
        root / "README.md",
        root / updater.CONFIG.manual_relative,
        root / updater.CONFIG.excluded_relative,
        root / updater.CONFIG.candidates_relative,
        root / "rule/QuantumultX/EtherFi/EtherFi.list",
        root / "rule/QuantumultX/EtherFi/README.md",
        root / "scripts/update_etherfi_quantumultx.py",
        root / "scripts/validate_etherfi_rules.py",
        root / "tests/test_etherfi_rules.py",
        root / ".github/workflows/update-etherfi-quantumultx.yml",
    )
    private_scheme = re.compile(r"(?i)\b(?:vless|vmess|trojan|ss)://")
    for path in etherfi_public_paths:
        if not path.is_file():
            errors.append(f"{path}: required EtherFi project file is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if private_scheme.search(text):
            errors.append(f"{path}: contains a private subscription scheme")
        for issue in utils.find_privacy_issues(text):
            errors.append(f"{path}: contains personal or region-specific wording: {issue}")
    return errors


def main() -> int:
    errors, rules = utils.validate_service(
        updater.CONFIG,
        root=ROOT,
        extra_checks=extra_checks,
    )
    if errors:
        print("EtherFi validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    counts = utils.count_rules(rules["main"])
    print(
        "EtherFi validation passed: "
        f"{counts['TOTAL']} main rules "
        f"(HOST={counts['HOST']}, HOST-SUFFIX={counts['HOST-SUFFIX']}, "
        f"IP-CIDR={counts['IP-CIDR']}, IP6-CIDR={counts['IP6-CIDR']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
