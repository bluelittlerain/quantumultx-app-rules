from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import quantumultx_rule_utils as utils  # noqa: E402
import update_coca_quantumultx as updater  # noqa: E402
from rule_test_helpers import CommonRuleTestsMixin  # noqa: E402


class CommonCOCARuleTests(CommonRuleTestsMixin, unittest.TestCase):
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
        return self.url or "https://www.coca.xyz/"


def official_page(extra: str = "") -> str:
    return (
        "<!doctype html><html><head><title>COCA Wallet</title></head><body>"
        + ("official COCA crypto card and wallet public content " * 80)
        + extra
        + "</body></html>"
    )


class COCAScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = (ROOT / updater.CONFIG.manual_relative).read_text(encoding="utf-8")
        cls.entries = utils.parse_manual(text, {"coca-core"})
        cls.exclusions = utils.parse_exclusions(
            (ROOT / updater.CONFIG.excluded_relative).read_text(encoding="utf-8")
        )

    def test_only_approved_core_rules_are_in_main(self) -> None:
        self.assertEqual(
            [entry.rule for entry in self.entries],
            [
                utils.Rule("HOST", "wwallet.app.link"),
                utils.Rule("HOST-SUFFIX", "coca.xyz"),
            ],
        )

    def test_parent_covers_confirmed_coca_hosts(self) -> None:
        roots = [entry.rule for entry in self.entries]
        for host in (
            "api-prod.coca.xyz",
            "docs.coca.xyz",
            "help.coca.xyz",
            "status.coca.xyz",
            "www.coca.xyz",
        ):
            rules = utils.process_rules([*roots, utils.Rule("HOST", host)])
            self.assertNotIn(utils.Rule("HOST", host), rules)

    def test_coca_cola_and_homonym_domains_are_rejected(self) -> None:
        approved = {entry.rule.value for entry in self.entries}
        for domain in (
            "coca-cola.com",
            "coca-colacompany.com",
            "coca.com",
        ):
            with self.subTest(domain=domain):
                self.assertIn(domain, self.exclusions)
                self.assertNotIn(domain, approved)
                self.assertEqual(updater._approved_observation(domain), [])

    def test_public_cdn_root_is_rejected(self) -> None:
        for root in ("cloudfront.net", "cloudflare.net", "amazonaws.com"):
            with self.subTest(root=root):
                with self.assertRaises(utils.SafetyError):
                    utils.process_rules([utils.Rule("HOST-SUFFIX", root)])

    def test_shared_wirex_and_other_products_do_not_enter_main(self) -> None:
        approved = {entry.rule.value for entry in self.entries}
        for domain in (
            "api-baas.wirexapp.com",
            "one.wirexapp.com",
            "wirex.app.link",
            "wirexapp.com",
            "wirexone.freshdesk.com",
        ):
            with self.subTest(domain=domain):
                self.assertNotIn(domain, approved)

    def test_entire_wirex_root_is_explicitly_excluded(self) -> None:
        self.assertIn("wirexapp.com", self.exclusions)
        self.assertNotIn(
            utils.Rule("HOST-SUFFIX", "wirexapp.com"),
            [entry.rule for entry in self.entries],
        )

    def test_shared_financial_identity_and_web3_roots_stay_out(self) -> None:
        approved = {entry.rule.value for entry in self.entries}
        for domain in (
            "mastercard.com",
            "privy.io",
            "sumsub.com",
            "visa.com",
            "walletconnect.com",
            "walletconnect.org",
        ):
            with self.subTest(domain=domain):
                self.assertIn(domain, self.exclusions)
                self.assertNotIn(domain, approved)

    def test_exact_branch_tenant_is_confirmed_without_parent_suffix(self) -> None:
        approved = [entry.rule for entry in self.entries]
        self.assertIn(utils.Rule("HOST", "wwallet.app.link"), approved)
        self.assertNotIn(utils.Rule("HOST-SUFFIX", "app.link"), approved)

    def test_no_unsubstantiated_optional_outputs(self) -> None:
        self.assertEqual([spec.scope for spec in updater.CONFIG.outputs], ["coca-core"])
        for name in ("COCA-Web3.list", "COCA-Regional.list"):
            self.assertFalse((ROOT / "rule/QuantumultX/COCA" / name).exists())

    def test_minimum_rule_floor_is_not_one(self) -> None:
        self.assertGreaterEqual(updater.CONFIG.minimum_upstream_rules, 2)
        self.assertGreaterEqual(updater.CONFIG.outputs[0].minimum_rules, 2)

    def test_updater_uses_current_public_official_sources(self) -> None:
        self.assertGreaterEqual(len(updater.CONFIG.upstream_urls), 7)
        self.assertIn("https://status.coca.xyz/", updater.CONFIG.upstream_urls)
        for url in updater.CONFIG.upstream_urls:
            host = updater.urllib.parse.urlsplit(url).hostname
            self.assertIsNotNone(host)
            self.assertTrue(updater._allowed_source_host(host or ""))

    def test_official_html_yields_conservative_observations(self) -> None:
        page = official_page(
            '<a href="https://wwallet.app.link/open">Open app</a>'
            '<script src="https://static.wixstatic.com/shared.js"></script>'
            '<a href="https://api-baas.wirexapp.com/">Shared Wirex</a>'
            '<a href="https://www.coca-cola.com/">Other brand</a>'
        )
        with mock.patch.object(
            updater.urllib.request,
            "urlopen",
            return_value=FakeHtmlResponse(page),
        ):
            result = updater.fetch_official_observations(
                "https://www.coca.xyz/",
                "test-agent",
                10,
            )
        rules = utils.parse_upstream(result)
        self.assertIn(utils.Rule("HOST-SUFFIX", "coca.xyz"), rules)
        self.assertIn(utils.Rule("HOST", "www.coca.xyz"), rules)
        self.assertIn(utils.Rule("HOST", "wwallet.app.link"), rules)
        self.assertNotIn(utils.Rule("HOST", "static.wixstatic.com"), rules)
        self.assertNotIn(utils.Rule("HOST", "api-baas.wirexapp.com"), rules)
        self.assertNotIn(utils.Rule("HOST", "www.coca-cola.com"), rules)

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
                    "https://www.coca.xyz/", "test-agent", 10
                )

    def test_official_fetch_rejects_branded_error_page(self) -> None:
        page = (
            "<!doctype html><html><head><title>COCA - Page Not Found</title>"
            "</head><body>"
            + ("COCA crypto wallet card navigation " * 80)
            + "</body></html>"
        )
        with mock.patch.object(
            updater.urllib.request,
            "urlopen",
            return_value=FakeHtmlResponse(page),
        ):
            with self.assertRaises(utils.UpstreamError):
                updater.fetch_official_observations(
                    "https://www.coca.xyz/", "test-agent", 10
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
                "https://www.coca.xyz/", "test-agent", 10
            )
        self.assertEqual(urlopen.call_count, 2)
        self.assertIn("coca.xyz", result)

    def test_official_fetch_rejects_external_redirect(self) -> None:
        response = FakeHtmlResponse(
            official_page(), url="https://shared.example.net/error"
        )
        with mock.patch.object(
            updater.urllib.request, "urlopen", return_value=response
        ):
            with self.assertRaises(utils.UpstreamError):
                updater.fetch_official_observations(
                    "https://www.coca.xyz/", "test-agent", 10
                )

    def test_public_url_query_and_fragment_are_removed(self) -> None:
        source = (
            "https://www.coca.xyz/privacy?" + "to" + "ken=redacted#section"
        )
        self.assertEqual(
            updater.sanitize_public_url(source),
            "https://www.coca.xyz/privacy",
        )

    def test_sensitive_scanner_detects_payment_card_number(self) -> None:
        value = "4111" + "1111" + "1111" + "1111"
        self.assertIn("payment card number", utils.find_sensitive(value))

    def test_sensitive_scanner_detects_iban(self) -> None:
        value = "GB29" + "NWBK" + "6016" + "1331" + "9268" + "19"
        self.assertIn("IBAN", utils.find_sensitive(value))

    def test_sensitive_scanner_detects_private_key_header(self) -> None:
        value = "-----BEGIN " + "PRIVATE KEY-----\nredacted"
        self.assertIn("private key", utils.find_sensitive(value))

    def test_sensitive_scanner_detects_mnemonic_phrase(self) -> None:
        words = [f"word{chr(97 + index)}" for index in range(12)]
        value = "seed" + " phrase: " + " ".join(words)
        self.assertIn("mnemonic or recovery phrase", utils.find_sensitive(value))

    def test_sensitive_scanner_detects_recovery_qr_payload(self) -> None:
        value = "recovery " + "QR payload: " + ("A1b2" * 10)
        self.assertIn("recovery QR payload", utils.find_sensitive(value))


if __name__ == "__main__":
    unittest.main()
