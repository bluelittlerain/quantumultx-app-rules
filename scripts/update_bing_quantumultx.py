#!/usr/bin/env python3
"""Update independent Microsoft Bing Quantumult X rule resources."""

from pathlib import Path

from quantumultx_rule_utils import AppConfig, OutputSpec, run_update_cli


ROOT = Path(__file__).resolve().parents[1]
CONFIG = AppConfig(
    policy="Bing",
    upstream_urls=(
        "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/bing",
        "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/bing.yaml",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Bing/Bing.list",
    ),
    minimum_upstream_rules=15,
    manual_relative="data/bing_manual_domains.txt",
    excluded_relative="data/bing_excluded_domains.txt",
    candidates_relative="data/bing_candidates.tsv",
    readme_relatives=(
        "README.md",
        "rule/QuantumultX/Bing/README.md",
    ),
    outputs=(
        OutputSpec(
            scope="main",
            relative_path="rule/QuantumultX/Bing/Bing.list",
            name="Bing",
            description="Microsoft Bing search app and service domain rules",
            source="Microsoft Bing public services, v2fly/domain-list-community, MetaCubeX/meta-rules-dat",
            minimum_rules=5,
            count_marker="BING_MAIN_COUNTS",
            updated_marker="BING_MAIN_UPDATED",
        ),
        OutputSpec(
            scope="ai",
            relative_path="rule/QuantumultX/Bing/Bing-AI.list",
            name="Bing AI",
            description="Optional Bing Copilot Search and AI service domain rules",
            source="Microsoft public Copilot services and current public upstream rules",
            minimum_rules=3,
            count_marker="BING_AI_COUNTS",
            updated_marker="BING_AI_UPDATED",
        ),
    ),
    user_agent_component="bing-updater",
)


if __name__ == "__main__":
    raise SystemExit(run_update_cli(CONFIG, root=ROOT))
