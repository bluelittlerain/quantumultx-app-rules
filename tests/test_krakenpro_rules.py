from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import quantumultx_rule_utils as utils  # noqa: E402
import update_krakenpro_quantumultx as updater  # noqa: E402
from rule_test_helpers import CommonRuleTestsMixin  # noqa: E402


class CommonKrakenProRuleTests(CommonRuleTestsMixin, unittest.TestCase):
    config = updater.CONFIG


class KrakenProScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / updater.CONFIG.manual_relative).read_text(encoding="utf-8")
        cls.entries = utils.parse_manual(text, {"main"})
        cls.exclusions = utils.parse_exclusions(
            (ROOT / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
        )

    def test_only_approved_first_party_roots_are_in_main(self) -> None:
        self.assertEqual(
            [entry.rule for entry in self.entries],
            [
                utils.Rule("HOST-SUFFIX", "kraken.com"),
                utils.Rule("HOST-SUFFIX", "kraken.onl"),
                utils.Rule("HOST-SUFFIX", "krakenpro.onl"),
            ],
        )

    def test_kraken_parent_covers_core_hosts(self) -> None:
        roots = [entry.rule for entry in self.entries]
        for host in (
            "api.kraken.com",
            "futures.kraken.com",
            "id.kraken.com",
            "ws-auth.kraken.com",
            "ws-l3.kraken.com",
            "ws.kraken.com",
        ):
            rules = utils.process_rules([*roots, utils.Rule("HOST", host)])
            self.assertNotIn(utils.Rule("HOST", host), rules)

    def test_brand_collisions_and_shared_services_are_excluded(self) -> None:
        for domain in (
            "cloudflare.com",
            "kraken.io",
            "kraken.pro",
            "kraken.tech",
            "kraken.zone",
            "onelink.me",
            "walletconnect.com",
        ):
            self.assertIn(domain, self.exclusions)

    def test_no_unsubstantiated_optional_outputs(self) -> None:
        self.assertEqual([spec.scope for spec in updater.CONFIG.outputs], ["main"])
        self.assertFalse(
            (ROOT / "rule/QuantumultX/KrakenPro/KrakenPro-Web3.list").exists()
        )
        self.assertFalse(
            (ROOT / "rule/QuantumultX/KrakenPro/KrakenPro-Regional.list").exists()
        )

    def test_updater_uses_current_kraken_specific_sources(self) -> None:
        self.assertEqual(len(updater.CONFIG.upstream_urls), 2)
        self.assertTrue(
            any(
                "domain-list-community" in url
                for url in updater.CONFIG.upstream_urls
            )
        )
        self.assertTrue(
            any("meta-rules-dat" in url for url in updater.CONFIG.upstream_urls)
        )


if __name__ == "__main__":
    unittest.main()
