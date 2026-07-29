#!/usr/bin/env python3
"""Validate OKX core and optional Web3 Quantumult X rules."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Sequence

import quantumultx_rule_utils as utils
import update_okx_quantumultx as updater


ROOT = Path(__file__).resolve().parents[1]


def extra_checks(
    rules_by_scope: Mapping[str, Sequence[utils.Rule]], root: Path
) -> list[str]:
    errors: list[str] = []
    main = list(rules_by_scope.get("main", ()))
    web3 = list(rules_by_scope.get("web3", ()))
    main_values = {rule.value for rule in main}
    web3_values = {rule.value for rule in web3}
    for forbidden in {"xlayer.tech", "oklink.com"}:
        if forbidden in main_values:
            errors.append(f"OKX main: Web3 domain mixed in: {forbidden}")
    if web3_values != {"oklink.com", "xlayer.tech"}:
        errors.append("OKX Web3 rules do not match the approved Web3 scope")
    for rule in main + web3:
        if "cloudflare.net" in rule.value:
            errors.append(f"OKX: Cloudflare CNAME was included: {rule.value}")
    required_dns = {"okx-dns.com", "okx-dns1.com", "okx-dns2.com"}
    if not required_dns.issubset(main_values):
        errors.append("OKX main: approved connection DNS roots are missing")
    candidates = (root / updater.CONFIG.candidates_relative).read_text(
        encoding="utf-8"
    )
    if (
        "okx.com.cdn.cloudflare.net\tHOST-SUFFIX\tshared\texcluded\t"
        not in candidates
    ):
        errors.append("OKX Cloudflare CNAME classification is missing")
    return errors


def main() -> int:
    errors, rules = utils.validate_service(
        updater.CONFIG, root=ROOT, extra_checks=extra_checks
    )
    if errors:
        print("OKX validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "OKX validation passed: "
        f"{len(rules['main'])} main and {len(rules['web3'])} Web3 rules."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
