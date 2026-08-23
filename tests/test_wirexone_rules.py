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


def observation_payload(url: str) -> str:
    host = updater.urllib.parse.urlsplit(url).hostname
    if not host:
        raise AssertionError("test source URL has no host")
    if host == "wirexone.freshdesk.com":
        return f"full:{host}\n"
    return f"full:{host}\n{updater.WIREX_ROOT}\n"


def source_fetcher(
    failures: dict[str, BaseException | str] | None = None,
    *,
    payload: str | None = None,
):
    failures = failures or {}

    def fetch(url: str, user_agent: str, timeout: int) -> str:
        failure = failures.get(url)
        if isinstance(failure, BaseException):
            raise failure
        if isinstance(failure, str):
            return failure
        return payload if payload is not None else observation_payload(url)

    return fetch


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
        self.assertEqual(len(updater.CORE_SOURCE_URLS), 3)
        self.assertEqual(len(updater.OPTIONAL_SOURCE_URLS), 2)
        self.assertEqual(
            updater.CONFIG.upstream_urls,
            updater.CORE_SOURCE_URLS + updater.OPTIONAL_SOURCE_URLS,
        )
        self.assertNotIn(
            "https://www.wirexapp.com/legal/one/privacy",
            updater.CONFIG.upstream_urls,
        )
        self.assertNotIn(
            "https://www.wirexapp.com/", updater.CONFIG.upstream_urls
        )
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

    def test_official_fetch_rejects_branded_error_page(self) -> None:
        page = (
            "<!doctype html><html><head><title>Wirex One - Page Not Found"
            "</title></head><body>"
            + ("Wirex One public navigation " * 80)
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

    def _assert_single_source_failure_is_degraded(
        self, exception_factory, reason: str
    ) -> None:
        failed_url = updater.CORE_SOURCE_URLS[0]
        failed_attempts = 0

        def urlopen(request, timeout):
            nonlocal failed_attempts
            if request.full_url == failed_url:
                failed_attempts += 1
                raise exception_factory()
            return FakeHtmlResponse(official_page(), url=request.full_url)

        with (
            mock.patch.object(
                updater.urllib.request, "urlopen", side_effect=urlopen
            ),
            mock.patch.object(updater.time, "sleep") as sleep,
        ):
            plan, sources = updater.prepare_resilient_update()
        self.assertEqual(len(sources.successful), 4)
        self.assertEqual(sources.core_successful, 2)
        self.assertEqual(sources.skipped, 1)
        self.assertIn(reason, sources.warnings[0].reason)
        self.assertEqual(failed_attempts, 3)
        self.assertEqual(sleep.call_count, 2)
        main = next(
            item for item in plan.files if item.path.name == "WirexOne.list"
        )
        self.assertEqual(main.removed, 0)
        self.assertEqual(main.old_content, main.new_content)

    def test_one_429_source_is_skipped_when_others_succeed(self) -> None:
        self._assert_single_source_failure_is_degraded(
            lambda: updater.urllib.error.HTTPError(
                updater.CORE_SOURCE_URLS[0],
                429,
                "Too Many Requests",
                {},
                None,
            ),
            "HTTP 429 Too Many Requests"
        )

    def test_one_403_source_is_skipped_when_others_succeed(self) -> None:
        self._assert_single_source_failure_is_degraded(
            lambda: updater.urllib.error.HTTPError(
                updater.CORE_SOURCE_URLS[0], 403, "Forbidden", {}, None
            ),
            "HTTP 403 Forbidden",
        )

    def test_one_500_source_is_skipped_when_others_succeed(self) -> None:
        self._assert_single_source_failure_is_degraded(
            lambda: updater.urllib.error.HTTPError(
                updater.CORE_SOURCE_URLS[0],
                500,
                "Internal Server Error",
                {},
                None,
            ),
            "HTTP 500 Internal Server Error"
        )

    def test_one_timeout_source_is_skipped_when_others_succeed(self) -> None:
        self._assert_single_source_failure_is_degraded(
            lambda: TimeoutError("timed out"),
            "temporary network error: timed out"
        )

    def test_truncated_response_is_skipped_when_others_succeed(self) -> None:
        self._assert_single_source_failure_is_degraded(
            lambda: updater.resilient.http.client.IncompleteRead(b"partial"),
            "temporary network error",
        )

    def test_one_malformed_source_is_skipped_when_others_succeed(self) -> None:
        failed_url = updater.CORE_SOURCE_URLS[0]
        plan, sources = updater.prepare_resilient_update(
            fetcher=source_fetcher({failed_url: "<html>broken</html>"})
        )
        self.assertEqual(sources.skipped, 1)
        self.assertIn("HTML", sources.warnings[0].reason)
        main = next(
            item for item in plan.files if item.path.name == "WirexOne.list"
        )
        self.assertEqual(main.old_content, main.new_content)

    def test_all_sources_failing_blocks_update_and_preserves_list(self) -> None:
        path = ROOT / "rule/QuantumultX/WirexOne/WirexOne.list"
        before = path.read_bytes()
        failures = {
            source.url: utils.UpstreamError("temporary network failure")
            for source in updater.DISCOVERY_SOURCES
        }
        with self.assertRaisesRegex(
            utils.SafetyError, "all official discovery sources failed"
        ):
            updater.prepare_resilient_update(fetcher=source_fetcher(failures))
        self.assertEqual(path.read_bytes(), before)

    def test_too_few_core_sources_blocks_update(self) -> None:
        successful = {
            updater.CORE_SOURCE_URLS[0],
            updater.OPTIONAL_SOURCE_URLS[0],
        }
        failures = {
            source.url: utils.UpstreamError("unavailable")
            for source in updater.DISCOVERY_SOURCES
            if source.url not in successful
        }
        with self.assertRaisesRegex(
            utils.SafetyError, "successful core sources 1"
        ):
            updater.prepare_resilient_update(fetcher=source_fetcher(failures))

    def test_too_few_observations_blocks_update(self) -> None:
        with self.assertRaisesRegex(utils.SafetyError, "observation count 1"):
            updater.prepare_resilient_update(
                fetcher=source_fetcher(payload="wirexapp.com\n")
            )

    def test_partial_failure_keeps_manual_rules(self) -> None:
        failed_url = updater.CORE_SOURCE_URLS[0]
        plan, _ = updater.prepare_resilient_update(
            fetcher=source_fetcher(
                {failed_url: utils.UpstreamError("HTTP 503 Service Unavailable")}
            )
        )
        main = next(
            item for item in plan.files if item.path.name == "WirexOne.list"
        )
        self.assertIn(
            "HOST,wirexone.freshdesk.com,WirexOne", main.new_content
        )
        self.assertIn(
            "HOST-SUFFIX,wirexapp.com,WirexOne", main.new_content
        )
        self.assertEqual(main.removed, 0)

    def test_unchanged_resilient_update_preserves_timestamp(self) -> None:
        plan, _ = updater.prepare_resilient_update(fetcher=source_fetcher())
        main = next(
            item for item in plan.files if item.path.name == "WirexOne.list"
        )
        self.assertFalse(main.body_changed)
        self.assertEqual(main.old_content, main.new_content)

    def test_429_retry_count_is_limited(self) -> None:
        url = updater.CORE_SOURCE_URLS[0]
        error = updater.urllib.error.HTTPError(
            url, 429, "Too Many Requests", {}, None
        )
        with (
            mock.patch.object(
                updater.urllib.request,
                "urlopen",
                side_effect=[error, error, error],
            ) as urlopen,
            mock.patch.object(updater.time, "sleep") as sleep,
        ):
            with self.assertRaises(updater.resilient.SourceFetchError):
                updater.fetch_official_observations(url, "test-agent", 10)
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_retry_after_above_limit_skips_without_waiting(self) -> None:
        url = updater.CORE_SOURCE_URLS[0]
        error = updater.urllib.error.HTTPError(
            url,
            429,
            "Too Many Requests",
            {"Retry-After": "120"},
            None,
        )
        with (
            mock.patch.object(
                updater.urllib.request, "urlopen", side_effect=error
            ) as urlopen,
            mock.patch.object(updater.time, "sleep") as sleep,
        ):
            with self.assertRaisesRegex(
                updater.resilient.SourceFetchError,
                "exceeds 10s limit",
            ):
                updater.fetch_official_observations(url, "test-agent", 10)
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()

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
