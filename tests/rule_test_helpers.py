"""Reusable unittest coverage for independent maintained rule entry points."""

from __future__ import annotations

import dataclasses
import datetime as dt
import tempfile
from pathlib import Path

import quantumultx_rule_utils as utils


def upstream_payload(count: int = 5) -> str:
    return "payload:\n" + "".join(
        f"  - +.upstream-{index}.example.net\n" for index in range(count)
    )


class CommonRuleTestsMixin:
    config: utils.AppConfig

    def test_domain_converts_to_host(self) -> None:
        self.assertEqual(
            utils.make_rule("DOMAIN", "api.service.example"),
            utils.Rule("HOST", "api.service.example"),
        )

    def test_domain_suffix_converts_to_host_suffix(self) -> None:
        self.assertEqual(
            utils.make_rule("DOMAIN-SUFFIX", "service.example"),
            utils.Rule("HOST-SUFFIX", "service.example"),
        )

    def test_full_converts_to_host(self) -> None:
        self.assertEqual(
            utils.parse_upstream("full:api.service.example\n"),
            [utils.Rule("HOST", "api.service.example")],
        )

    def test_ipv6_converts_to_ip6_cidr(self) -> None:
        self.assertEqual(
            utils.make_rule("IP-CIDR6", "2001:db8::1/48"),
            utils.Rule("IP6-CIDR", "2001:db8::/48"),
        )

    def test_duplicate_is_removed(self) -> None:
        rule = utils.Rule("HOST-SUFFIX", "service.example")
        self.assertEqual(utils.process_rules([rule, rule]), [rule])

    def test_case_duplicate_is_removed(self) -> None:
        self.assertEqual(
            utils.process_rules(
                [
                    utils.Rule("HOST-SUFFIX", "Service.Example"),
                    utils.Rule("HOST-SUFFIX", "service.example"),
                ]
            ),
            [utils.Rule("HOST-SUFFIX", "service.example")],
        )

    def test_trailing_dot_is_removed(self) -> None:
        self.assertEqual(
            utils.make_rule("HOST", "api.service.example."),
            utils.Rule("HOST", "api.service.example"),
        )

    def test_parent_suffix_removes_redundant_host(self) -> None:
        self.assertEqual(
            utils.process_rules(
                [
                    utils.Rule("HOST-SUFFIX", "service.example"),
                    utils.Rule("HOST", "api.service.example"),
                ]
            ),
            [utils.Rule("HOST-SUFFIX", "service.example")],
        )

    def test_forbidden_shared_root_is_rejected(self) -> None:
        with self.assertRaises(utils.SafetyError):
            utils.process_rules(
                [utils.Rule("HOST-SUFFIX", "cloudfront.net")]
            )

    def _test_config(self) -> utils.AppConfig:
        spec = dataclasses.replace(
            self.config.outputs[0],
            relative_path="rule.list",
            minimum_rules=2,
            count_marker="TEST_COUNTS",
            updated_marker="TEST_UPDATED",
        )
        return dataclasses.replace(
            self.config,
            upstream_urls=("https://source.invalid/rules",),
            minimum_upstream_rules=2,
            manual_relative="manual.txt",
            excluded_relative="excluded.txt",
            candidates_relative="candidates.tsv",
            readme_relatives=("README.md",),
            outputs=(spec,),
        )

    def _make_project(self, root: Path) -> utils.AppConfig:
        config = self._test_config()
        (root / "manual.txt").write_text(
            "# type,domain,scope,source\n"
            "HOST-SUFFIX,approved-one.example.net,main,official public source\n"
            "HOST-SUFFIX,approved-two.example.net,main,official public source\n",
            encoding="utf-8",
        )
        (root / "excluded.txt").write_text(
            "# domain,reason\nblocked.example.net,not approved\n",
            encoding="utf-8",
        )
        (root / "candidates.tsv").write_text(
            "\t".join(utils.CANDIDATE_HEADER)
            + "\n"
            + "candidate.example.net\tHOST-SUFFIX\tmain\tconfirmed\t"
            "https://source.invalid/rules\tpublic candidate\tlow\t"
            "must not enter automatically\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text(
            "# Test\n\n"
            "<!-- TEST_COUNTS_START -->0 rules<!-- TEST_COUNTS_END -->\n"
            "<!-- TEST_UPDATED_START -->2026-01-01 00:00:00 UTC"
            "<!-- TEST_UPDATED_END -->\n",
            encoding="utf-8",
        )
        return config

    @staticmethod
    def _fetch_ok(url: str, user_agent: str, timeout: int) -> str:
        return upstream_payload()

    def test_candidate_does_not_enter_formal_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self._make_project(root)
            plan = utils.prepare_update(
                config, root=root, fetcher=self._fetch_ok
            )
            output = next(item for item in plan.files if item.path.name == "rule.list")
            self.assertNotIn("candidate.example.net", output.new_content)
            self.assertIn("approved-one.example.net", output.new_content)

    def test_excluded_rule_is_removed(self) -> None:
        rules = utils.apply_exclusions(
            [
                utils.Rule("HOST-SUFFIX", "allowed.example.net"),
                utils.Rule("HOST-SUFFIX", "blocked.example.net"),
            ],
            {"blocked.example.net": "not approved"},
        )
        self.assertEqual(
            rules, [utils.Rule("HOST-SUFFIX", "allowed.example.net")]
        )

    def test_empty_upstream_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self._make_project(root)
            output = root / "rule.list"
            output.write_text("existing\n", encoding="utf-8")
            with self.assertRaises(utils.UpstreamError):
                utils.prepare_update(
                    config,
                    root=root,
                    fetcher=lambda url, agent, timeout: "",
                )
            self.assertEqual(output.read_text(encoding="utf-8"), "existing\n")

    def test_html_upstream_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self._make_project(root)
            output = root / "rule.list"
            output.write_text("existing\n", encoding="utf-8")
            with self.assertRaises(utils.UpstreamError):
                utils.prepare_update(
                    config,
                    root=root,
                    fetcher=lambda url, agent, timeout: "<html>error</html>",
                )
            self.assertEqual(output.read_text(encoding="utf-8"), "existing\n")

    def test_network_failure_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self._make_project(root)
            output = root / "rule.list"
            output.write_text("existing\n", encoding="utf-8")

            def fail(url: str, agent: str, timeout: int) -> str:
                raise utils.UpstreamError("network unavailable")

            with self.assertRaises(utils.UpstreamError):
                utils.prepare_update(config, root=root, fetcher=fail)
            self.assertEqual(output.read_text(encoding="utf-8"), "existing\n")

    def test_abnormal_output_decline_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self._make_project(root)
            old_rules = [
                utils.Rule("HOST-SUFFIX", f"old-{index}.example.net")
                for index in range(10)
            ]
            old_content, _, _ = utils.render_rule_file(
                spec=config.outputs[0],
                policy=config.policy,
                rules=old_rules,
                old_content="",
                now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
            )
            (root / "rule.list").write_text(old_content, encoding="utf-8")
            with self.assertRaises(utils.SafetyError):
                utils.prepare_update(
                    config, root=root, fetcher=self._fetch_ok
                )

    def test_generated_header_counts_are_correct(self) -> None:
        rules = [
            utils.Rule("HOST", "api.service.example"),
            utils.Rule("HOST-SUFFIX", "service.example"),
        ]
        content, _, _ = utils.render_rule_file(
            spec=self.config.outputs[0],
            policy=self.config.policy,
            rules=rules,
            old_content="",
            now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
        )
        counts = utils.parse_header(content)
        self.assertEqual(counts["HOST"], 1)
        self.assertEqual(counts["HOST-SUFFIX"], 1)
        self.assertEqual(counts["TOTAL"], 2)

    def test_unchanged_body_preserves_timestamp(self) -> None:
        rules = [utils.Rule("HOST-SUFFIX", "service.example")]
        old, _, old_time = utils.render_rule_file(
            spec=self.config.outputs[0],
            policy=self.config.policy,
            rules=rules,
            old_content="",
            now=dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
        )
        new, changed, new_time = utils.render_rule_file(
            spec=self.config.outputs[0],
            policy=self.config.policy,
            rules=rules,
            old_content=old,
            now=dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc),
        )
        self.assertFalse(changed)
        self.assertEqual(old_time, new_time)
        self.assertEqual(old, new)

    def test_readme_region_recommendation_is_detected(self) -> None:
        phrase = "建议选择" + "台湾" + "节点"
        self.assertTrue(utils.find_privacy_issues(phrase))

    def test_sensitive_scanner_detects_uuid(self) -> None:
        value = "12345678" + "-1234" + "-4abc" + "-8def" + "-1234567890ab"
        self.assertIn("UUID-like credential", utils.find_sensitive(value))

    def test_sensitive_scanner_detects_token_parameter(self) -> None:
        value = "https://service.example/path?" + "to" + "ken=secret-value"
        self.assertIn("sensitive URL parameter", utils.find_sensitive(value))

    def test_sensitive_scanner_detects_password_assignment(self) -> None:
        value = "pass" + "word=secret-value"
        self.assertIn("password assignment", utils.find_sensitive(value))

    def test_manual_rule_survives_upstream_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self._make_project(root)
            plan = utils.prepare_update(
                config, root=root, fetcher=self._fetch_ok
            )
            output = next(item for item in plan.files if item.path.name == "rule.list")
            self.assertIn("approved-one.example.net", output.new_content)
            self.assertNotIn("upstream-0.example.net", output.new_content)
