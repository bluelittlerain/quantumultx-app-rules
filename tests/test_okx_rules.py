from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import quantumultx_rule_utils as utils  # noqa: E402
import update_okx_quantumultx as updater  # noqa: E402
from rule_test_helpers import CommonRuleTestsMixin  # noqa: E402


class CommonOKXRuleTests(CommonRuleTestsMixin, unittest.TestCase):
    config = updater.CONFIG


class OKXScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / updater.CONFIG.manual_relative).read_text(encoding="utf-8")
        cls.entries = utils.parse_manual(
            text, {spec.scope for spec in updater.CONFIG.outputs}
        )

    def test_core_and_web3_are_separate(self) -> None:
        main = {entry.rule.value for entry in self.entries if entry.scope == "main"}
        web3 = {entry.rule.value for entry in self.entries if entry.scope == "web3"}
        self.assertTrue(main.isdisjoint(web3))

    def test_xlayer_is_not_in_core(self) -> None:
        main = {entry.rule.value for entry in self.entries if entry.scope == "main"}
        self.assertNotIn("xlayer.tech", main)

    def test_oklink_is_in_web3(self) -> None:
        web3 = {entry.rule.value for entry in self.entries if entry.scope == "web3"}
        self.assertIn("oklink.com", web3)

    def test_cloudflare_root_is_rejected(self) -> None:
        with self.assertRaises(utils.SafetyError):
            utils.process_rules(
                [utils.Rule("HOST-SUFFIX", "cloudflare.net")]
            )

    def test_cloudflare_cname_is_excluded(self) -> None:
        exclusions = utils.parse_exclusions(
            (ROOT / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
        )
        self.assertIn("okx.com.cdn.cloudflare.net", exclusions)


if __name__ == "__main__":
    unittest.main()
