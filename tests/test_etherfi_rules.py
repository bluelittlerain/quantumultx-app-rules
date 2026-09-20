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
        return self.url or "https://www.ether.fi/"


def official_page(extra: str = "") -> str:
    return (
        "<!doctype html><html><head><title>Ether.fi</title></head><body>"
        + ("official Ether.fi staking cash liquid help content " * 80)
        + extra
        + "</body></html>"
    )


def observation_payload(url: str) -> str:
    del url
    return "ether.fi\n"


def source_fetcher(
    failures: dict[str, BaseException | str] | None = None,
    *,
    payload: str | None = None,
):
    failures = failures or {}

    def fetch(url: str, user_agent: str, timeout: int) -> str:
        del user_agent, timeout
        failure = failures.get(url)
        if isinstance(failure, BaseException):
            raise failure
        if isinstance(failure, str):
            return failure
        return payload if payload is not None else observation_payload(url)

    return fetch


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

    def test_updater_uses_reduced_tiered_official_sources(self) -> None:
        self.assertEqual(
            updater.CORE_SOURCE_URLS,
            (
                "https://www.ether.fi/",
                "https://help.ether.fi/en/",
            ),
        )
        self.assertEqual(
            updater.OPTIONAL_SOURCE_URLS,
            ("https://etherfi.gitbook.io/etherfi",),
        )
        self.assertEqual(
            updater.CONFIG.upstream_urls,
            updater.CORE_SOURCE_URLS + updater.OPTIONAL_SOURCE_URLS,
        )
        for redundant in ("/stake", "/liquid", "/cash"):
            self.assertFalse(
                any(url.endswith(redundant) for url in updater.CONFIG.upstream_urls)
            )

    def test_source_success_threshold_replaces_redundant_host_observations(
        self,
    ) -> None:
        self.assertEqual(updater.CONFIG.minimum_upstream_rules, 1)
        self.assertEqual(updater.MINIMUM_SUCCESSFUL_SOURCES, 2)
        self.assertEqual(updater.MINIMUM_CORE_SOURCES, 1)
        self.assertEqual(
            updater._approved_observation("help.ether.fi"),
            [utils.Rule("HOST-SUFFIX", "ether.fi")],
        )

    def test_official_html_yields_conservative_observations(self) -> None:
        page = official_page(
            '<a href="https://help.ether.fi/en/">Help</a>'
            '<a href="https://walletconnect.org/">Shared</a>'
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
        self.assertNotIn(utils.Rule("HOST", "help.ether.fi"), rules)
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
                "https://www.ether.fi/",
                "test-agent",
                10,
            )
        self.assertEqual(urlopen.call_count, 2)
        self.assertIn("ether.fi", result)

    def test_official_fetch_rejects_branded_error_page(self) -> None:
        page = (
            "<!doctype html><html><head><title>Ether.fi - Page Not Found</title>"
            "</head><body>"
            + ("official Ether.fi navigation " * 80)
            + "</body></html>"
        )
        with mock.patch.object(
            updater.urllib.request,
            "urlopen",
            return_value=FakeHtmlResponse(page),
        ):
            with self.assertRaises(utils.UpstreamError):
                updater.fetch_official_observations(
                    "https://www.ether.fi/", "test-agent", 10
                )

    def test_official_fetch_rejects_external_redirect(self) -> None:
        response = FakeHtmlResponse(
            official_page(), url="https://shared.example.net/error"
        )
        with mock.patch.object(
            updater.urllib.request, "urlopen", return_value=response
        ):
            with self.assertRaises(utils.UpstreamError):
                updater.fetch_official_observations(
                    "https://www.ether.fi/", "test-agent", 10
                )

    def _assert_single_source_failure_is_degraded(
        self, exception_factory, reason: str
    ) -> None:
        failed_url = updater.CORE_SOURCE_URLS[0]
        failed_attempts = 0

        def urlopen(request, timeout):
            del timeout
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
        self.assertEqual(len(sources.successful), 2)
        self.assertEqual(sources.core_successful, 1)
        self.assertEqual(sources.skipped, 1)
        self.assertIn(reason, sources.warnings[0].reason)
        self.assertEqual(failed_attempts, 3)
        self.assertEqual(sleep.call_count, 2)
        main = next(
            item for item in plan.files if item.path.name == "EtherFi.list"
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
            "HTTP 429 Too Many Requests",
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
            "HTTP 500 Internal Server Error",
        )

    def test_one_timeout_source_is_skipped_when_others_succeed(self) -> None:
        self._assert_single_source_failure_is_degraded(
            lambda: TimeoutError("timed out"),
            "temporary network error: timed out",
        )

    def test_incomplete_read_source_is_skipped_when_others_succeed(self) -> None:
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
            item for item in plan.files if item.path.name == "EtherFi.list"
        )
        self.assertEqual(main.old_content, main.new_content)

    def test_retry_after_below_limit_waits_then_retries(self) -> None:
        url = updater.CORE_SOURCE_URLS[0]
        error = updater.urllib.error.HTTPError(
            url,
            429,
            "Too Many Requests",
            {"Retry-After": "2"},
            None,
        )
        with (
            mock.patch.object(
                updater.urllib.request,
                "urlopen",
                side_effect=[error, FakeHtmlResponse(official_page(), url=url)],
            ) as urlopen,
            mock.patch.object(updater.time, "sleep") as sleep,
        ):
            result = updater.fetch_official_observations(url, "test-agent", 10)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(2.0)
        self.assertEqual(
            utils.parse_upstream(result),
            [utils.Rule("HOST-SUFFIX", "ether.fi")],
        )

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

    def test_optional_sources_may_all_fail_when_core_is_sufficient(self) -> None:
        failures = {
            url: utils.UpstreamError("optional unavailable")
            for url in updater.OPTIONAL_SOURCE_URLS
        }
        plan, sources = updater.prepare_resilient_update(
            fetcher=source_fetcher(failures)
        )
        self.assertEqual(sources.core_successful, 2)
        self.assertEqual(len(sources.successful), 2)
        self.assertEqual(sources.skipped, len(updater.OPTIONAL_SOURCE_URLS))
        main = next(
            item for item in plan.files if item.path.name == "EtherFi.list"
        )
        self.assertEqual(main.old_content, main.new_content)

    def test_too_few_core_sources_blocks_update(self) -> None:
        failures = {
            url: utils.UpstreamError("core unavailable")
            for url in updater.CORE_SOURCE_URLS
        }
        with self.assertRaisesRegex(
            utils.SafetyError, "successful core sources 0"
        ):
            updater.prepare_resilient_update(
                fetcher=source_fetcher(failures)
            )

    def test_all_sources_failing_blocks_update_and_preserves_list(self) -> None:
        path = ROOT / "rule/QuantumultX/EtherFi/EtherFi.list"
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

    def test_insufficient_observations_blocks_update(self) -> None:
        path = ROOT / "rule/QuantumultX/EtherFi/EtherFi.list"
        before = path.read_bytes()
        with self.assertRaisesRegex(
            utils.SafetyError, "observation count 0 is below safety minimum 1"
        ):
            updater.prepare_resilient_update(
                fetcher=source_fetcher(payload="# no supported observations\n")
            )
        self.assertEqual(path.read_bytes(), before)

    def test_partial_failure_keeps_manual_rule(self) -> None:
        failed_url = updater.CORE_SOURCE_URLS[0]
        plan, _ = updater.prepare_resilient_update(
            fetcher=source_fetcher(
                {failed_url: utils.UpstreamError("HTTP 503 Service Unavailable")}
            )
        )
        main = next(
            item for item in plan.files if item.path.name == "EtherFi.list"
        )
        self.assertIn("HOST-SUFFIX,ether.fi,EtherFi", main.new_content)
        self.assertEqual(main.removed, 0)

    def test_unchanged_resilient_update_preserves_timestamp(self) -> None:
        plan, _ = updater.prepare_resilient_update(fetcher=source_fetcher())
        main = next(
            item for item in plan.files if item.path.name == "EtherFi.list"
        )
        self.assertFalse(main.body_changed)
        self.assertEqual(main.old_content, main.new_content)

    def test_parent_suffix_does_not_generate_redundant_formal_hosts(self) -> None:
        plan, _ = updater.prepare_resilient_update(fetcher=source_fetcher())
        main = next(
            item for item in plan.files if item.path.name == "EtherFi.list"
        )
        body = utils.parse_rule_body(main.new_content, updater.CONFIG.policy)
        self.assertEqual(body, [utils.Rule("HOST-SUFFIX", "ether.fi")])

    def test_candidates_do_not_enter_resilient_formal_output(self) -> None:
        plan, _ = updater.prepare_resilient_update(fetcher=source_fetcher())
        main = next(
            item for item in plan.files if item.path.name == "EtherFi.list"
        )
        self.assertNotIn("etherfi.gitbook.io", main.new_content)
        self.assertNotIn("etherfi.onelink.me", main.new_content)

    def test_shared_wallet_rpc_and_cdn_observations_are_rejected(self) -> None:
        for domain in (
            "privy.io",
            "walletconnect.org",
            "polygon-rpc.com",
            "cloudflare.com",
            "amazonaws.com",
        ):
            with self.subTest(domain=domain):
                self.assertEqual(updater._approved_observation(domain), [])

    def test_public_url_query_and_fragment_are_removed(self) -> None:
        source = "https://www.ether.fi/stake?" + "to" + "ken=redacted#section"
        self.assertEqual(
            updater.sanitize_public_url(source),
            "https://www.ether.fi/stake",
        )


if __name__ == "__main__":
    unittest.main()
