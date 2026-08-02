from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import quantumultx_rule_utils as utils  # noqa: E402
import update_wirexone_quantumultx as updater  # noqa: E402
from rule_test_helpers import CommonRuleTestsMixin  # noqa: E402


class CommonWirexOneRuleTests(CommonRuleTestsMixin, unittest.TestCase):
    config = updater.CONFIG


class FakeHtmlResponse:
    def __init__(self, text: str, url: str | None = None) -> None:
        self.payload = text.encode("utf-8")
        self.url = url
        self.headers = {"Content-Type": "text/html; charset=utf-8"}

    def __enter__(self) -> FakeHtmlResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]

    def geturl(self) -> str:
        return self.url or "https://www.wirexapp.com/"


def official_page(extra: str = "") -> str:
    return (
        "<!doctype html><html><head><title>Wirex One</title></head><body>"
        + ("official Wirex One public content " * 80)
        + extra
        + "</body></html>"
    )


class WirexOneScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / updater.CONFIG.manual_relative).read_text(encoding="utf-8")
        cls.entries = utils.parse_manual(text, {"wirexone-core"})
        cls.exclusions = utils.parse_exclusions(
            (ROOT / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
        )

    def test_only_approved_core_rules_are_in_main(self) -> None:
        self.assertEqual(
            [entry.rule for entry in self.entries],
            [
                utils.Rule("HOST", "wirexone.freshdesk.com"),
                utils.Rule("HOST-SUFFIX", "wirexapp.com"),
            ],
        )

    def test_parent_covers_confirmed_wirex_hosts(self) -> None:
        roots = [entry.rule for entry in self.entries]
        for host in (
            "api-baas.wirexapp.com",
            "cdn.wirexapp.com",
            "help.wirexapp.com",
            "one.wirexapp.com",
            "resourses.wirexapp.com",
            "status.wirexapp.com",
            "wx-acquiring-card-manager.wirexapp.com",
        ):
            rules = utils.process_rules([*roots, utils.Rule("HOST", host)])
            self.assertNotIn(utils.Rule("HOST", host), rules)

    def test_financial_wallet_and_identity_roots_are_rejected(self) -> None:
        for root in (
            "mastercard.com",
            "paypal.com",
            "privy.io",
            "stripe.com",
            "visa.com",
            "walletconnect.com",
        ):
            with self.subTest(root=root):
                with self.assertRaises(utils.SafetyError):
                    utils.process_rules([utils.Rule("HOST-SUFFIX", root)])

    def test_shared_and_unconfirmed_services_are_excluded(self) -> None:
        for domain in (
            "amazonaws.com",
            "app.link",
            "arc.network",
            "freshdesk.com",
            "privy.io",
            "sumsub.com",
            "visa.com",
            "wirex.app.link",
            "wirex.com",
            "wirexapp.tech",
            "wirexpaychain.com",
        ):
            self.assertIn(domain, self.exclusions)

    def test_classic_candidate_does_not_enter_main(self) -> None:
        approved = {entry.rule.value for entry in self.entries}
        self.assertNotIn("wirex.app.link", approved)
        candidates = (ROOT / updater.CONFIG.candidates_relative).read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "wirex.app.link\tHOST\tclassic-wirex\tneeds-review\t",
            candidates,
        )

    def test_shared_kyc_card_and_web3_candidates_do_not_enter_main(self) -> None:
        approved = {entry.rule.value for entry in self.entries}
        for domain in (
            "mastercard.com",
            "privy.io",
            "sumsub.com",
            "visa.com",
            "walletconnect.com",
        ):
            self.assertNotIn(domain, approved)

    def test_no_unsubstantiated_optional_outputs(self) -> None:
        self.assertEqual(
            [spec.scope for spec in updater.CONFIG.outputs], ["wirexone-core"]
        )
        for name in ("WirexOne-Web3.list", "WirexOne-Regional.list"):
            self.assertFalse(
                (ROOT / "rule/QuantumultX/WirexOne" / name).exists()
            )

    def test_minimum_rule_floor_is_not_one(self) -> None:
        self.assertGreaterEqual(updater.CONFIG.minimum_upstream_rules, 2)
        self.assertGreaterEqual(updater.CONFIG.outputs[0].minimum_rules, 2)

    def test_updater_uses_only_current_public_official_sources(self) -> None:
        self.assertGreaterEqual(len(updater.CONFIG.upstream_urls), 6)
        self.assertIn("https://one.wirexapp.com/", updater.CONFIG.upstream_urls)
        for url in updater.CONFIG.upstream_urls:
            host = updater.urllib.parse.urlsplit(url).hostname
            self.assertIsNotNone(host)
            self.assertTrue(updater._allowed_source_host(host or ""))

    def test_official_html_yields_conservative_observations(self) -> None:
        page = official_page(
            '<a href="https://wirexone.freshdesk.com/support/">Help</a>'
            '<script src="https://static.wixstatic.com/shared.js"></script>'
            '<a href="https://auth.privy.io/">Identity</a>'
        )
        with mock.patch.object(
            updater.urllib.request,
            "urlopen",
            return_value=FakeHtmlResponse(page),
        ):
            result = updater.fetch_official_observations(
                "https://www.wirexapp.com/",
                "test-agent",
                10,
            )
        rules = utils.parse_upstream(result)
        self.assertIn(utils.Rule("HOST-SUFFIX", "wirexapp.com"), rules)
        self.assertIn(utils.Rule("HOST", "www.wirexapp.com"), rules)
        self.assertIn(utils.Rule("HOST", "wirexone.freshdesk.com"), rules)
        self.assertNotIn(utils.Rule("HOST", "auth.privy.io"), rules)
        self.assertNotIn(utils.Rule("HOST", "static.wixstatic.com"), rules)

    def test_official_fetch_rejects_wrong_identity_page(self) -> None:
        page = (
            "<!doctype html><html><head><title>Error</title></head><body>"
            + ("unexpected public response " * 80)
            + "</body></html>"
        )
        with mock.patch.object(
            updater.urllib.request,
            "urlopen",
            return_value=FakeHtmlResponse(page),
        ):
            with self.assertRaises(utils.UpstreamError):
                updater.fetch_official_observations(
                    "https://www.wirexapp.com/", "test-agent", 10
                )

    def test_official_fetch_retries_network_error(self) -> None:
        with (
            mock.patch.object(
                updater.urllib.request,
                "urlopen",
                side_effect=[
                    updater.urllib.error.URLError("temporary"),
                    FakeHtmlResponse(official_page()),
                ],
            ) as urlopen,
            mock.patch.object(updater.time, "sleep"),
        ):
            result = updater.fetch_official_observations(
                "https://www.wirexapp.com/", "test-agent", 10
            )
        self.assertEqual(urlopen.call_count, 2)
        self.assertIn("wirexapp.com", result)

    def test_official_fetch_rejects_external_redirect(self) -> None:
        response = FakeHtmlResponse(
            official_page(), url="https://shared.example.net/error"
        )
        with mock.patch.object(
            updater.urllib.request, "urlopen", return_value=response
        ):
            with self.assertRaises(utils.UpstreamError):
                updater.fetch_official_observations(
                    "https://www.wirexapp.com/", "test-agent", 10
                )

    def test_public_url_query_and_fragment_are_removed(self) -> None:
        source = (
            "https://www.wirexapp.com/legal/one/terms?"
            + "to"
            + "ken=redacted#section"
        )
        self.assertEqual(
            updater.sanitize_public_url(source),
            "https://www.wirexapp.com/legal/one/terms",
        )

    def test_sensitive_scanner_detects_payment_card_number(self) -> None:
        value = "4111" + "1111" + "1111" + "1111"
        self.assertIn("payment card number", utils.find_sensitive(value))

    def test_sensitive_scanner_detects_iban(self) -> None:
        value = "GB29" + "NWBK" + "6016" + "1331" + "9268" + "19"
        self.assertIn("IBAN", utils.find_sensitive(value))

    def test_sensitive_scanner_detects_labeled_phone_number(self) -> None:
        value = "phone" + " number: +44 " + "7700 900123"
        self.assertIn("phone number", utils.find_sensitive(value))


if __name__ == "__main__":
    unittest.main()
