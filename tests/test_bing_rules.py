from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import quantumultx_rule_utils as utils  # noqa: E402
import update_bing_quantumultx as updater  # noqa: E402
from rule_test_helpers import CommonRuleTestsMixin  # noqa: E402


class CommonBingRuleTests(CommonRuleTestsMixin, unittest.TestCase):
    config = updater.CONFIG


class BingScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / updater.CONFIG.manual_relative).read_text(encoding="utf-8")
        cls.entries = utils.parse_manual(
            text, {spec.scope for spec in updater.CONFIG.outputs}
        )

    def test_search_and_ai_are_separate(self) -> None:
        main = {entry.rule.value for entry in self.entries if entry.scope == "main"}
        ai = {entry.rule.value for entry in self.entries if entry.scope == "ai"}
        self.assertTrue(main.isdisjoint(ai))

    def test_microsoft_suffix_is_rejected(self) -> None:
        with self.assertRaises(utils.SafetyError):
            utils.process_rules(
                [utils.Rule("HOST-SUFFIX", "microsoft.com")]
            )

    def test_live_suffix_is_rejected(self) -> None:
        with self.assertRaises(utils.SafetyError):
            utils.process_rules([utils.Rule("HOST-SUFFIX", "live.com")])

    def test_ads_and_telemetry_are_not_approved(self) -> None:
        values = {entry.rule.value for entry in self.entries}
        self.assertNotIn("bingads.com", values)
        self.assertNotIn("bingapistatistics.com", values)

    def test_exact_microsoft_host_is_allowed(self) -> None:
        rule = utils.Rule("HOST", "location.microsoft.com")
        self.assertEqual(utils.process_rules([rule]), [rule])


if __name__ == "__main__":
    unittest.main()
