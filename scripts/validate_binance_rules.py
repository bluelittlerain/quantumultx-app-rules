#!/usr/bin/env python3
"""Validate Binance core, ecosystem, and regional Quantumult X rules."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Sequence

import quantumultx_rule_utils as utils
import update_binance_quantumultx as updater


ROOT = Path(__file__).resolve().parents[1]


def extra_checks(
    rules_by_scope: Mapping[str, Sequence[utils.Rule]], root: Path
) -> list[str]:
    errors: list[str] = []
    main = list(rules_by_scope.get("main", ()))
    ecosystem = list(rules_by_scope.get("ecosystem", ()))
    regional = list(rules_by_scope.get("regional", ()))
    for rule in main:
        if rule.value == "binance.us":
            errors.append("Binance main: Binance.US must remain regional")
        if rule.value.startswith("binancezh.") or rule.value in {
            "bnappzh.co",
            "bnbzh.ac",
        }:
            errors.append(f"Binance main: historical mirror included: {rule.value}")
        if rule.value == "appsflayer.com":
            errors.append("Binance main: unverified appsflayer.com is forbidden")
        if rule.kind == "HOST-SUFFIX" and rule.value in {
            "appsflyer.com",
            "appsflyersdk.com",
        }:
            errors.append("Binance main: shared AppsFlyer suffix is forbidden")
        if rule.value in {"bnbchain.org", "nftstatic.com", "binance.charity"}:
            errors.append(f"Binance main: ecosystem domain mixed in: {rule.value}")
    for rule in main:
        if rule.value.endswith(".appsflyersdk.com") and rule.kind != "HOST":
            errors.append("Binance main: AppsFlyer integration must use exact HOST")
    if {rule.value for rule in regional} != {"binance.us"}:
        errors.append("Binance regional rules must contain only approved Binance.US")
    if not {"bnbchain.org", "nftstatic.com"}.issubset(
        {rule.value for rule in ecosystem}
    ):
        errors.append("Binance ecosystem rules are missing approved domains")
    candidates = (root / updater.CONFIG.candidates_relative).read_text(
        encoding="utf-8"
    )
    if not candidates.startswith(
        "domain\trule_type\tscope\tstatus\tsource\tevidence\trisk\tnotes\n"
    ):
        errors.append("Binance candidate file header is invalid")
    if "appsflayer.com\tHOST-SUFFIX\tshared\thistorical\t" not in candidates:
        errors.append("Binance appsflayer.com review is not recorded")
    return errors


def main() -> int:
    errors, rules = utils.validate_service(
        updater.CONFIG, root=ROOT, extra_checks=extra_checks
    )
    if errors:
        print("Binance validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "Binance validation passed: "
        f"{len(rules['main'])} main, {len(rules['ecosystem'])} ecosystem, "
        f"{len(rules['regional'])} regional rules."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
