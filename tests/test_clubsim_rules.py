from __future__ import annotations

import datetime as dt
import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import discover_clubsim_domains as discover  # noqa: E402
import update_clubsim_quantumultx as updater  # noqa: E402
import validate_clubsim_rules as validator  # noqa: E402


UPSTREAM_TEXT = """\
# NAME: ClubSim
DOMAIN,csl.prod.ondemandconnectivity.com
DOMAIN,hhk.prod.ondemandconnectivity.com
DOMAIN,epdg.epc.mnc000.mcc454.pub.3gppnetwork.org
DOMAIN,ss.epdg.epc.mnc000.mcc454.pub.3gppnetwork.org
DOMAIN,ss.epdg.epc.geo.mnc000.mcc454.pub.3gppnetwork.org
"""

MANUAL_TEXT = """\
# 类型,域名,范围,来源说明
HOST,clubsim.page.link,prepaid-app,official app-link script
HOST-SUFFIX,clubsim.com.hk,prepaid-app,official website and APIs
"""

NETWORK_TEXT = """\
# 类型,域名,范围,来源说明
HOST,csl.prod.ondemandconnectivity.com,network,public ClubSim network rule
HOST,epdg.epc.mnc000.mcc454.pub.3gppnetwork.org,network,public ClubSim network rule
HOST,hhk.prod.ondemandconnectivity.com,network,public ClubSim network rule
HOST,ss.epdg.epc.geo.mnc000.mcc454.pub.3gppnetwork.org,network,public ClubSim network rule
HOST,ss.epdg.epc.mnc000.mcc454.pub.3gppnetwork.org,network,public ClubSim network rule
"""

EXCLUDED_TEXT = """\
# 域名或根域名,排除原因
api.whatsapp.com,shared messaging endpoint
google.com,shared identity platform
"""

CANDIDATE_HEADER = (
    "domain\trule_type\tscope\tstatus\tsource\tevidence\trisk\tnotes\n"
)


class TempProject:
    def __init__(
        self,
        root: Path,
        *,
        manual: str = MANUAL_TEXT,
        network: str = NETWORK_TEXT,
        excluded: str = EXCLUDED_TEXT,
        candidates: str = CANDIDATE_HEADER,
    ) -> None:
        self.root = root
        self.paths = updater.ProjectPaths(
            main_rule=root / "ClubSim.list",
            network_rule=root / "ClubSim-Network.list",
            manual=root / "clubsim_manual_domains.txt",
            network_data=root / "clubsim_network_domains.txt",
            excluded=root / "clubsim_excluded_domains.txt",
            candidates=root / "clubsim_candidates.tsv",
            readmes=(),
        )
        self.paths.manual.write_text(manual, encoding="utf-8")
        self.paths.network_data.write_text(network, encoding="utf-8")
        self.paths.excluded.write_text(excluded, encoding="utf-8")
        self.paths.candidates.write_text(candidates, encoding="utf-8")

    def write_existing(self) -> None:
        timestamp = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        main_rules = updater.parse_approved_data(
            self.paths.manual.read_text(encoding="utf-8"), "prepaid-app"
        )
        network_rules = updater.parse_approved_data(
            self.paths.network_data.read_text(encoding="utf-8"), "network"
        )
        main, _, _ = updater.render_rule_file(
            name="ClubSim",
            description="Club Sim prepaid app account and service rules",
            source="Club Sim official website and official app static resources",
            rules=main_rules,
            old_content="",
            now=timestamp,
        )
        network, _, _ = updater.render_rule_file(
            name="ClubSim Network",
            description="Club Sim optional eSIM, ePDG and network-service rules",
            source="ClearLuv/iOS_collecton ClubSim public rule",
            rules=network_rules,
            old_content="",
            now=timestamp,
        )
        self.paths.main_rule.write_text(main, encoding="utf-8")
        self.paths.network_rule.write_text(network, encoding="utf-8")


class RuleTransformationTests(unittest.TestCase):
    def test_domain_converts_to_host(self) -> None:
        rule = updater.make_rule("DOMAIN", "www.clubsim.com.hk")
        self.assertEqual(rule, updater.Rule("HOST", "www.clubsim.com.hk"))

    def test_domain_suffix_converts_to_host_suffix(self) -> None:
        rule = updater.make_rule("DOMAIN-SUFFIX", "clubsim.com.hk")
        self.assertEqual(rule, updater.Rule("HOST-SUFFIX", "clubsim.com.hk"))

    def test_ipv6_converts_to_ip6_cidr(self) -> None:
        rule = updater.make_rule("IP-CIDR6", "2001:db8::1/64")
        self.assertEqual(rule, updater.Rule("IP6-CIDR", "2001:db8::/64"))

    def test_exact_duplicate_is_removed(self) -> None:
        rule = updater.Rule("HOST", "clubsim.page.link")
        self.assertEqual(updater.deduplicate_rules([rule, rule]), [rule])

    def test_case_duplicate_is_removed(self) -> None:
        rules = [
            updater.make_rule("HOST", "ClubSim.Page.Link"),
            updater.make_rule("HOST", "clubsim.page.link"),
        ]
        self.assertEqual(len(updater.deduplicate_rules(rules)), 1)

    def test_trailing_dot_is_removed(self) -> None:
        rule = updater.make_rule("HOST-SUFFIX", "ClubSim.com.hk.")
        self.assertEqual(rule.value, "clubsim.com.hk")

    def test_parent_suffix_removes_redundant_host(self) -> None:
        rules = [
            updater.make_rule("HOST", "api.clubsim.com.hk"),
            updater.make_rule("HOST-SUFFIX", "clubsim.com.hk"),
        ]
        self.assertEqual(
            updater.collapse_parent_coverage(rules),
            [updater.Rule("HOST-SUFFIX", "clubsim.com.hk")],
        )

    def test_shared_root_is_rejected(self) -> None:
        with self.assertRaises(updater.SafetyError):
            updater.validate_rule_allowed(
                updater.make_rule("HOST-SUFFIX", "google.com")
            )

    def test_clubsim_root_is_accepted(self) -> None:
        rule = updater.make_rule("HOST-SUFFIX", "clubsim.com.hk")
        updater.validate_rule_allowed(rule)
        self.assertEqual(rule.value, "clubsim.com.hk")

    def test_rule_counts_and_total_are_correct(self) -> None:
        rules = [
            updater.make_rule("HOST", "clubsim.page.link"),
            updater.make_rule("HOST-SUFFIX", "clubsim.com.hk"),
        ]
        counts = updater.count_rules(rules)
        self.assertEqual(counts["HOST"], 1)
        self.assertEqual(counts["HOST-SUFFIX"], 1)
        self.assertEqual(counts["TOTAL"], 2)


class SafeUpdateTests(unittest.TestCase):
    def _build(self, project: TempProject) -> updater.ProjectUpdate:
        return updater.build_update(
            paths=project.paths,
            fetcher=lambda _: UPSTREAM_TEXT,
            now=dt.datetime(2026, 2, 2, tzinfo=dt.timezone.utc),
        )

    def test_network_domains_are_separate_from_main_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory))
            update = self._build(project)
            self.assertFalse(
                {rule.value for rule in update.main.new_rules}
                & updater.NETWORK_DOMAINS
            )
            self.assertEqual(
                {rule.value for rule in update.network.new_rules},
                set(updater.NETWORK_DOMAINS),
            )

    def test_candidates_do_not_enter_formal_rules(self) -> None:
        candidates = (
            CANDIDATE_HEADER
            + "unverified.invalid.test\tHOST\tunknown\tneeds-review\t"
            "https://www.clubsim.com.hk/\tpublic string\tmedium\tnot approved\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory), candidates=candidates)
            update = self._build(project)
            values = {rule.value for rule in update.main.new_rules}
            self.assertNotIn("unverified.invalid.test", values)

    def test_monthly_candidate_does_not_enter_prepaid_rules(self) -> None:
        candidates = (
            CANDIDATE_HEADER
            + "monthly.invalid.test\tHOST\tmonthly-app\tneeds-review\t"
            "https://play.google.com/store/apps/details\tlisting\tmedium\tcandidate\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory), candidates=candidates)
            update = self._build(project)
            self.assertEqual(update.monthly_candidate_count, 1)
            self.assertNotIn(
                "monthly.invalid.test",
                {rule.value for rule in update.main.new_rules},
            )

    def test_empty_upstream_does_not_overwrite_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory))
            project.write_existing()
            before = project.paths.main_rule.read_bytes()
            with self.assertRaises(updater.UpstreamError):
                updater.build_update(
                    paths=project.paths, fetcher=lambda _: ""
                )
            self.assertEqual(project.paths.main_rule.read_bytes(), before)

    def test_html_upstream_does_not_overwrite_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory))
            project.write_existing()
            before = project.paths.network_rule.read_bytes()
            with self.assertRaises(updater.UpstreamError):
                updater.build_update(
                    paths=project.paths,
                    fetcher=lambda _: "<!doctype html><html>Error</html>",
                )
            self.assertEqual(project.paths.network_rule.read_bytes(), before)

    def test_network_failure_does_not_overwrite_existing_files(self) -> None:
        def fail(_: str) -> str:
            raise updater.UpstreamError("simulated public network failure")

        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory))
            project.write_existing()
            before = project.paths.main_rule.read_bytes()
            with self.assertRaises(updater.UpstreamError):
                updater.build_update(paths=project.paths, fetcher=fail)
            self.assertEqual(project.paths.main_rule.read_bytes(), before)

    def test_abnormal_upstream_decline_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory))
            with self.assertRaises(updater.UpstreamError):
                updater.build_update(
                    paths=project.paths,
                    fetcher=lambda _: "DOMAIN,csl.prod.ondemandconnectivity.com\n",
                )

    def test_unchanged_body_preserves_timestamp(self) -> None:
        rules = updater.parse_approved_data(MANUAL_TEXT, "prepaid-app")
        old, _, old_time = updater.render_rule_file(
            name="ClubSim",
            description="Club Sim prepaid app account and service rules",
            source="Club Sim official website and official app static resources",
            rules=rules,
            old_content="",
            now=dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc),
        )
        new, changed, new_time = updater.render_rule_file(
            name="ClubSim",
            description="Club Sim prepaid app account and service rules",
            source="Club Sim official website and official app static resources",
            rules=rules,
            old_content=old,
            now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
        )
        self.assertFalse(changed)
        self.assertEqual(new_time, old_time)
        self.assertEqual(new, old)

    def test_manual_rule_survives_upstream_update(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory))
            update = self._build(project)
            self.assertIn(
                updater.Rule("HOST", "clubsim.page.link"),
                update.main.new_rules,
            )

    def test_exact_exclusion_blocks_shared_candidate(self) -> None:
        manual = MANUAL_TEXT + (
            "HOST,api.whatsapp.com,prepaid-app,public support link\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            project = TempProject(Path(directory), manual=manual)
            update = self._build(project)
            self.assertNotIn(
                "api.whatsapp.com",
                {rule.value for rule in update.main.new_rules},
            )

    def test_generated_header_total_is_correct(self) -> None:
        rules = updater.parse_approved_data(MANUAL_TEXT, "prepaid-app")
        content, _, _ = updater.render_rule_file(
            name="ClubSim",
            description="Club Sim prepaid app account and service rules",
            source="Club Sim official website and official app static resources",
            rules=rules,
            old_content="",
            now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
        )
        self.assertIn("# HOST: 1", content)
        self.assertIn("# HOST-SUFFIX: 1", content)
        self.assertIn("# TOTAL: 2", content)


class DiscoveryTests(unittest.TestCase):
    def test_url_query_and_fragment_are_removed(self) -> None:
        private_parameter = "tok" + "en=redacted"
        clean = discover.sanitize_url(
            "https://www.clubsim.com.hk/en/login?"
            + private_parameter
            + "#step"
        )
        self.assertEqual(clean, "https://www.clubsim.com.hk/en/login")

    def test_candidate_report_source_has_no_query(self) -> None:
        candidate = discover.classify_host(
            "clubsim.page.link",
            "https://www.clubsim.com.hk/en/app.js?build=public#code",
            evidence="official script",
        )
        rendered = discover.render_candidates([candidate])
        self.assertNotIn("?build=", rendered)
        self.assertNotIn("#code", rendered)

    def test_internal_hosts_are_not_public_candidates(self) -> None:
        self.assertFalse(discover.is_public_domain_candidate("localhost"))
        self.assertFalse(discover.is_public_domain_candidate("10.0.0.1"))
        self.assertFalse(discover.is_public_domain_candidate("a"))
        self.assertTrue(discover.is_public_domain_candidate("clubsim.com.hk"))

    def test_dedicated_dynamic_link_is_confirmed(self) -> None:
        candidate = discover.classify_host(
            "clubsim.page.link",
            "https://www.clubsim.com.hk/en/app.js",
            evidence="official script",
        )
        self.assertEqual(candidate.status, "confirmed")
        self.assertEqual(candidate.scope, "prepaid-app")
        self.assertEqual(candidate.rule_type, "HOST")

    def test_official_apk_static_inspection_verifies_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "ClubSim v2.3.9 [Prod][200167].apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr(
                    "AndroidManifest.xml",
                    b"com.pccw.clubsim https://api.clubsim.com.hk/v1",
                )
            report = discover.inspect_apk_file(
                apk,
                "https://www.clubsim.com.hk/api/apk/"
                "ClubSim%20v2.3.9%20%5BProd%5D%5B200167%5D.apk",
            )
            self.assertTrue(report.package_verified)
            self.assertEqual(report.version, "2.3.9")
            self.assertEqual(report.version_code, "200167")
            self.assertEqual(report.sha256, hashlib.sha256(apk.read_bytes()).hexdigest().upper())
            self.assertIn("api.clubsim.com.hk", report.domains)


class PrivacyValidationTests(unittest.TestCase):
    def test_sensitive_scanner_detects_uuid(self) -> None:
        value = "-".join(
            ("12345678", "1234", "4abc", "8abc", "1234567890ab")
        )
        self.assertIn("UUID-like credential", validator.find_sensitive(value))

    def test_sensitive_scanner_detects_token_parameter(self) -> None:
        value = "https://service.invalid/path?" + "tok" + "en=secretvalue"
        self.assertIn("sensitive URL parameter", validator.find_sensitive(value))

    def test_sensitive_scanner_detects_password_field(self) -> None:
        value = "pass" + "word=secretvalue"
        self.assertIn("sensitive assignment", validator.find_sensitive(value))

    def test_readmes_have_no_region_specific_proxy_recommendation(self) -> None:
        for path in (ROOT / "README.md", ROOT / "rule" / "QuantumultX" / "ClubSim" / "README.md"):
            if path.exists():
                text = path.read_text(encoding="utf-8")
                self.assertEqual(validator.validate_public_privacy(path, text), [])

    def test_bybit_rule_files_still_exist(self) -> None:
        self.assertTrue(
            (ROOT / "rule" / "QuantumultX" / "Bybit" / "Bybit.list").is_file()
        )
        self.assertTrue(
            (
                ROOT
                / "rule"
                / "QuantumultX"
                / "Bybit"
                / "Bybit-Regional.list"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()
