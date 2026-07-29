#!/usr/bin/env python3
"""Update independent OKX Quantumult X rule resources."""

from pathlib import Path

from quantumultx_rule_utils import AppConfig, OutputSpec, run_update_cli


ROOT = Path(__file__).resolve().parents[1]
CONFIG = AppConfig(
    policy="OKX",
    upstream_urls=(
        "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/okx",
        "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/okx.yaml",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/OKX/OKX.list",
    ),
    minimum_upstream_rules=7,
    manual_relative="data/okx_manual_domains.txt",
    excluded_relative="data/okx_excluded_domains.txt",
    candidates_relative="data/okx_candidates.tsv",
    readme_relatives=(
        "README.md",
        "rule/QuantumultX/OKX/README.md",
    ),
    outputs=(
        OutputSpec(
            scope="main",
            relative_path="rule/QuantumultX/OKX/OKX.list",
            name="OKX",
            description="OKX official app and service domain rules",
            source="OKX official API documentation, v2fly/domain-list-community, MetaCubeX/meta-rules-dat",
            minimum_rules=6,
            count_marker="OKX_MAIN_COUNTS",
            updated_marker="OKX_MAIN_UPDATED",
        ),
        OutputSpec(
            scope="web3",
            relative_path="rule/QuantumultX/OKX/OKX-Web3.list",
            name="OKX Web3",
            description="Optional OKX Web3, X Layer, and OKLink domain rules",
            source="OKX public Web3 services and current public upstream rules",
            minimum_rules=2,
            count_marker="OKX_WEB3_COUNTS",
            updated_marker="OKX_WEB3_UPDATED",
        ),
    ),
    user_agent_component="okx-updater",
)


if __name__ == "__main__":
    raise SystemExit(run_update_cli(CONFIG, root=ROOT))
