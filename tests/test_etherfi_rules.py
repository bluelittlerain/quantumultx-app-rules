from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import quantumultx_rule_utils as utils  # noqa: E402
import update_etherfi_quantumultx as updater  # noqa: E402
from rule_test_helpers import CommonRuleTestsMixin  # noqa: E402


class CommonEtherFiRuleTests(CommonRuleTestsMixin, unittest.TestCase):
    config = updater.CONFIG


class FakeHtmlResponse:
    def __init__(self, text: str) -> None:
        self.payload = text.encode("utf-8")
        self.headers = {"Content-Type": "text/html; charset=utf-8"}

    def __enter__(self) -> FakeHtmlResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


class EtherFiScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / updater.CONFIG.manual_relative).read_text(encoding="utf-8")
        cls.entries = utils.parse_manual(text, {"main"})
        cls.exclusions = utils.parse_exclusions(
            (ROOT / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
        )

    def test_only_first_party_root_is_approved(self) -> None:
        self.assertEqual(
            [entry.rule for entry in self.entries],
            [utils.Rule("HOST-SUFFIX", "ether.fi")],
        )

    def test_shared_wallet_services_are_excluded(self) -> None:
        for domain in ("reown.com", "walletconnect.com", "walletconnect.org"):
            self.assertIn(domain, self.exclusions)

    def test_external_documentation_is_not_approved(self) -> None:
        approved = {entry.rule.value for entry in self.entries}
        self.assertNotIn("etherfi.gitbook.io", approved)

    def test_app_deep_link_is_not_approved(self) -> None:
        approved = {entry.rule.value for entry in self.entries}
        self.assertNotIn("etherfi.onelink.me", approved)

    def test_no_unsubstantiated_web3_output(self) -> None:
        self.assertEqual([spec.scope for spec in updater.CONFIG.outputs], ["main"])
        self.assertFalse(
            (ROOT / "rule/QuantumultX/EtherFi/EtherFi-Web3.list").exists()
        )

    def test_official_html_yields_conservative_observations(self) -> None:
        page = (
            "<!doctype html><html><head><title>ether.fi</title></head><body>"
            + ("official ether.fi content " * 80)
            + '<a href="https://help.ether.fi/en/">Help</a>'
            + '<a href="https://walletconnect.org/">Shared</a>'
            + "</body></html>"
        )
        with mock.patch.object(
            updater.urllib.request,
            "urlopen",
            return_value=FakeHtmlResponse(page),
        ):
            result = updater.fetch_official_observations(
                "https://www.ether.fi/",
                "test-agent",
                10,
            )
        rules = utils.parse_upstream(result)
        self.assertIn(utils.Rule("HOST-SUFFIX", "ether.fi"), rules)
        self.assertIn(utils.Rule("HOST", "help.ether.fi"), rules)
        self.assertNotIn(utils.Rule("HOST-SUFFIX", "walletconnect.org"), rules)

    def test_official_fetch_rejects_wrong_identity_page(self) -> None:
        page = (
            "<!doctype html><html><head><title>Error</title></head><body>"
            + ("unexpected response " * 80)
            + "</body></html>"
        )
        with mock.patch.object(
            updater.urllib.request,
            "urlopen",
            return_value=FakeHtmlResponse(page),
        ):
            with self.assertRaises(utils.UpstreamError):
                updater.fetch_official_observations(
                    "https://www.ether.fi/",
                    "test-agent",
                    10,
                )

    def test_official_fetch_retries_transient_network_error(self) -> None:
        page = (
            "<!doctype html><html><head><title>ether.fi</title></head><body>"
            + ("official ether.fi content " * 80)
            + "</body></html>"
        )
        with (
            mock.patch.object(
                updater.urllib.request,
                "urlopen",
                side_effect=[
                    updater.urllib.error.URLError("temporary"),
                    FakeHtmlResponse(page),
                ],
            ) as urlopen,
            mock.patch.object(updater.time, "sleep"),
        ):
            result = updater.fetch_official_observations(
                "https://www.ether.fi/",
                "test-agent",
                10,
            )
        self.assertEqual(urlopen.call_count, 2)
        self.assertIn("ether.fi", result)


if __name__ == "__main__":
    unittest.main()
