#!/usr/bin/env python3
"""Update independent Binance Quantumult X rule resources."""

from pathlib import Path

from quantumultx_rule_utils import AppConfig, OutputSpec, run_update_cli


ROOT = Path(__file__).resolve().parents[1]
CONFIG = AppConfig(
    policy="Binance",
    upstream_urls=(
        "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/binance",
        "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/binance.yaml",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Binance/Binance.list",
    ),
    minimum_upstream_rules=20,
    manual_relative="data/binance_manual_domains.txt",
    excluded_relative="data/binance_excluded_domains.txt",
    candidates_relative="data/binance_candidates.tsv",
    readme_relatives=(
        "README.md",
        "rule/QuantumultX/Binance/README.md",
    ),
    outputs=(
        OutputSpec(
            scope="main",
            relative_path="rule/QuantumultX/Binance/Binance.list",
            name="Binance",
            description="Binance official app and service domain rules",
            source="Binance official documentation, v2fly/domain-list-community, MetaCubeX/meta-rules-dat",
            minimum_rules=10,
            count_marker="BINANCE_MAIN_COUNTS",
            updated_marker="BINANCE_MAIN_UPDATED",
        ),
        OutputSpec(
            scope="ecosystem",
            relative_path="rule/QuantumultX/Binance/Binance-Ecosystem.list",
            name="Binance Ecosystem",
            description="Optional Binance ecosystem and BNB Chain domain rules",
            source="Binance public services, v2fly/domain-list-community, MetaCubeX/meta-rules-dat",
            minimum_rules=3,
            count_marker="BINANCE_ECOSYSTEM_COUNTS",
            updated_marker="BINANCE_ECOSYSTEM_UPDATED",
        ),
        OutputSpec(
            scope="regional",
            relative_path="rule/QuantumultX/Binance/Binance-Regional.list",
            name="Binance Regional",
            description="Optional independent Binance regional service domain rules",
            source="Binance.US official website and current public upstream rules",
            minimum_rules=1,
            count_marker="BINANCE_REGIONAL_COUNTS",
            updated_marker="BINANCE_REGIONAL_UPDATED",
        ),
    ),
    user_agent_component="binance-updater",
)


if __name__ == "__main__":
    raise SystemExit(run_update_cli(CONFIG, root=ROOT))
