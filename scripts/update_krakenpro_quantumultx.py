#!/usr/bin/env python3
"""Update the independent Kraken Pro Quantumult X rule resource."""

from pathlib import Path

from quantumultx_rule_utils import AppConfig, OutputSpec, run_update_cli


ROOT = Path(__file__).resolve().parents[1]
CONFIG = AppConfig(
    policy="KrakenPro",
    upstream_urls=(
        "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/kraken",
        "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/kraken.yaml",
    ),
    minimum_upstream_rules=2,
    manual_relative="data/krakenpro_manual_domains.txt",
    excluded_relative="data/krakenpro_excluded_domains.txt",
    candidates_relative="data/krakenpro_candidates.tsv",
    readme_relatives=(
        "README.md",
        "rule/QuantumultX/KrakenPro/README.md",
    ),
    outputs=(
        OutputSpec(
            scope="main",
            relative_path="rule/QuantumultX/KrakenPro/KrakenPro.list",
            name="KrakenPro",
            description="Kraken Pro official app and service domain rules",
            source=(
                "Kraken official documentation, v2fly/domain-list-community, "
                "MetaCubeX/meta-rules-dat"
            ),
            minimum_rules=3,
            count_marker="KRAKENPRO_MAIN_COUNTS",
            updated_marker="KRAKENPRO_MAIN_UPDATED",
        ),
    ),
    user_agent_component="krakenpro-updater",
)


if __name__ == "__main__":
    raise SystemExit(run_update_cli(CONFIG, root=ROOT))
