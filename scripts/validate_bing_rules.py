#!/usr/bin/env python3
"""Validate Microsoft Bing search and optional AI Quantumult X rules."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Sequence

import quantumultx_rule_utils as utils
import update_bing_quantumultx as updater


ROOT = Path(__file__).resolve().parents[1]


def extra_checks(
    rules_by_scope: Mapping[str, Sequence[utils.Rule]], root: Path
) -> list[str]:
    errors: list[str] = []
    main = list(rules_by_scope.get("main", ()))
    ai = list(rules_by_scope.get("ai", ()))
    main_values = {rule.value for rule in main}
    ai_values = {rule.value for rule in ai}
    for forbidden in {
        "microsoft.com",
        "live.com",
        "microsoftonline.com",
        "office.com",
        "azure.com",
        "azureedge.net",
        "bingads.com",
        "bingapistatistics.com",
        "copilot.com",
        "copilot.cloud.microsoft",
        "copilot.microsoft.com",
    }:
        if forbidden in main_values:
            errors.append(f"Bing main: forbidden or optional domain included: {forbidden}")
    for rule in ai:
        if rule.kind == "HOST-SUFFIX" and rule.value in {
            "microsoft.com",
            "live.com",
            "office.com",
        }:
            errors.append(f"Bing AI: broad Microsoft suffix included: {rule.value}")
    if ai_values != {
        "copilot.com",
        "copilot.cloud.microsoft",
        "copilot.microsoft.com",
    }:
        errors.append("Bing AI rules do not match the approved optional scope")
    candidates = (root / updater.CONFIG.candidates_relative).read_text(
        encoding="utf-8"
    )
    for expected in (
        "bingads.com\tHOST-SUFFIX\tads\texcluded\t",
        "bingapistatistics.com\tHOST-SUFFIX\ttelemetry\texcluded\t",
    ):
        if expected not in candidates:
            errors.append("Bing advertising or telemetry classification is missing")
    return errors


def main() -> int:
    errors, rules = utils.validate_service(
        updater.CONFIG, root=ROOT, extra_checks=extra_checks
    )
    if errors:
        print("Bing validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "Bing validation passed: "
        f"{len(rules['main'])} main and {len(rules['ai'])} optional AI rules."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
