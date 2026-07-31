#!/usr/bin/env python3
"""Validate Kraken Pro Quantumult X rules and reviewed domain data."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Sequence

import quantumultx_rule_utils as utils
import update_krakenpro_quantumultx as updater


ROOT = Path(__file__).resolve().parents[1]


def extra_checks(
    rules_by_scope: Mapping[str, Sequence[utils.Rule]], root: Path
) -> list[str]:
    errors: list[str] = []
    main = list(rules_by_scope.get("main", ()))
    expected = [
        utils.Rule("HOST-SUFFIX", "kraken.com"),
        utils.Rule("HOST-SUFFIX", "kraken.onl"),
        utils.Rule("HOST-SUFFIX", "krakenpro.onl"),
    ]
    if main != expected:
        errors.append("KrakenPro main rules must match the three approved roots")

    if any(rule.kind in {"IP-CIDR", "IP6-CIDR"} for rule in main):
        errors.append("KrakenPro must not contain public IP ranges")

    for name in ("KrakenPro-Web3.list", "KrakenPro-Regional.list"):
        if (root / "rule" / "QuantumultX" / "KrakenPro" / name).exists():
            errors.append(f"unsubstantiated optional output exists: {name}")

    exclusions = utils.parse_exclusions(
        (root / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
    )
    for domain in {
        "cloudflare.com",
        "cloudfront.net",
        "krak.app",
        "kraken.io",
        "kraken.pro",
        "kraken.tech",
        "kraken.zone",
        "onelink.me",
        "walletconnect.com",
        "zendesk.com",
    }:
        if domain not in exclusions:
            errors.append(f"KrakenPro exclusion is missing: {domain}")

    candidates = (root / updater.CONFIG.candidates_relative).read_text(
        encoding="utf-8"
    )
    if not candidates.startswith("\t".join(utils.CANDIDATE_HEADER) + "\n"):
        errors.append("KrakenPro candidate file header is invalid")
    if "krakenpro.onl\tHOST-SUFFIX\tmain\tconfirmed\t" not in candidates:
        errors.append("Kraken Pro official deep-link review is not recorded")
    if "kraken.zone\tHOST-SUFFIX\tunknown\tneeds-review\t" not in candidates:
        errors.append("Kraken zone review status is not recorded")

    return errors


def main() -> int:
    errors, rules = utils.validate_service(
        updater.CONFIG, root=ROOT, extra_checks=extra_checks
    )
    if errors:
        print("Kraken Pro validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Kraken Pro validation passed: {len(rules['main'])} main rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
