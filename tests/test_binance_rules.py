from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import quantumultx_rule_utils as utils  # noqa: E402
import update_binance_quantumultx as updater  # noqa: E402
from rule_test_helpers import CommonRuleTestsMixin  # noqa: E402


class CommonBinanceRuleTests(CommonRuleTestsMixin, unittest.TestCase):
    config = updater.CONFIG


class BinanceScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / updater.CONFIG.manual_relative).read_text(encoding="utf-8")
        cls.entries = utils.parse_manual(
            text, {spec.scope for spec in updater.CONFIG.outputs}
        )

    def test_binance_us_is_not_in_global_main(self) -> None:
        main = {entry.rule.value for entry in self.entries if entry.scope == "main"}
        self.assertNotIn("binance.us", main)

    def test_historical_binancezh_is_not_in_main(self) -> None:
        main = {entry.rule.value for entry in self.entries if entry.scope == "main"}
        self.assertFalse(any(value.startswith("binancezh.") for value in main))

    def test_shared_appsflyer_suffix_is_rejected(self) -> None:
        for value in ("appsflyer.com", "appsflyersdk.com"):
            with self.assertRaises(utils.SafetyError):
                utils.process_rules([utils.Rule("HOST-SUFFIX", value)])

    def test_exact_appsflyer_host_is_allowed(self) -> None:
        rule = utils.Rule(
            "HOST", "zftksc.cdn-settings.appsflyersdk.com"
        )
        self.assertEqual(utils.process_rules([rule]), [rule])

    def test_unverified_appsflayer_is_not_approved(self) -> None:
        values = {entry.rule.value for entry in self.entries}
        self.assertNotIn("appsflayer.com", values)


if __name__ == "__main__":
    unittest.main()
