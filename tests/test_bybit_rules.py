from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_bybit_quantumultx as updater  # noqa: E402


def yaml_source(count: int, prefix: str = "upstream") -> str:
    lines = ["payload:"]
    lines.extend(f"  - +.{prefix}{index}.example" for index in range(count))
    return "\n".join(lines) + "\n"


class RuleConversionTests(unittest.TestCase):
    def test_domain_converts_to_host(self) -> None:
        rules = updater.parse_upstream("payload:\n  - DOMAIN,api.bybit.example\n")
        self.assertEqual(rules, [updater.Rule("HOST", "api.bybit.example")])

    def test_domain_suffix_converts_to_host_suffix(self) -> None:
        rules = updater.parse_upstream(
            "payload:\n  - DOMAIN-SUFFIX,bybit.example\n"
        )
        self.assertEqual(
            rules,
            [updater.Rule("HOST-SUFFIX", "bybit.example")],
        )

    def test_ipv6_cidr_converts_to_ip6_cidr(self) -> None:
        rules = updater.parse_upstream(
            "payload:\n  - IP-CIDR6,2001:db8::1/48,no-resolve\n"
        )
        self.assertEqual(
            rules,
            [updater.Rule("IP6-CIDR", "2001:db8::/48")],
        )

    def test_exact_duplicates_are_removed(self) -> None:
        rule = updater.Rule("HOST-SUFFIX", "bybit.example")
        self.assertEqual(updater.process_rules([rule, rule]), [rule])

    def test_case_duplicates_are_removed(self) -> None:
        rules = updater.process_rules(
            [
                updater.Rule("HOST-SUFFIX", "ByBit.Example"),
                updater.Rule("HOST-SUFFIX", "bybit.example."),
            ]
        )
        self.assertEqual(
            rules,
            [updater.Rule("HOST-SUFFIX", "bybit.example")],
        )

    def test_parent_suffix_removes_redundant_children(self) -> None:
        rules = updater.process_rules(
            [
                updater.Rule("HOST-SUFFIX", "bybit.example"),
                updater.Rule("HOST-SUFFIX", "api.bybit.example"),
                updater.Rule("HOST", "stream.bybit.example"),
                updater.Rule("HOST", "unrelated.example"),
            ]
        )
        self.assertEqual(
            rules,
            [
                updater.Rule("HOST", "unrelated.example"),
                updater.Rule("HOST-SUFFIX", "bybit.example"),
            ],
        )

    def test_forbidden_public_root_is_rejected(self) -> None:
        with self.assertRaises(updater.SafetyError):
            updater.process_rules(
                [updater.Rule("HOST-SUFFIX", "cloudfront.net")]
            )

    def test_statistics_are_correct(self) -> None:
        counts = updater.count_rules(
            [
                updater.Rule("HOST", "docs.bybit.example"),
                updater.Rule("HOST-SUFFIX", "bybit.example"),
                updater.Rule("IP-CIDR", "192.0.2.0/24"),
                updater.Rule("IP6-CIDR", "2001:db8::/32"),
            ]
        )
        self.assertEqual(
            counts,
            {
                "HOST": 1,
                "HOST-SUFFIX": 1,
                "IP-CIDR": 1,
                "IP6-CIDR": 1,
                "TOTAL": 4,
            },
        )


class SafeUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.output = self.base / "Bybit.list"
        self.manual = self.base / "manual.txt"
        self.excluded = self.base / "excluded.txt"
        self.manual.write_text("# TYPE,value,source\n", encoding="utf-8")
        self.excluded.write_text("# TYPE,value,reason\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prepare(self, text: str, **kwargs: object) -> updater.UpdateResult:
        return updater.prepare_update(
            output_path=self.output,
            manual_path=self.manual,
            excluded_path=self.excluded,
            fetcher=lambda: ("https://upstream.invalid/bybit.yaml", text),
            **kwargs,
        )

    def test_empty_upstream_does_not_overwrite_existing_file(self) -> None:
        original = "keep this existing rule file\n"
        self.output.write_text(original, encoding="utf-8")
        with self.assertRaises(updater.UpstreamError):
            self.prepare("")
        self.assertEqual(self.output.read_text(encoding="utf-8"), original)

    def test_html_error_page_does_not_overwrite_existing_file(self) -> None:
        original = "keep this existing rule file\n"
        self.output.write_text(original, encoding="utf-8")
        with self.assertRaises(updater.UpstreamError):
            self.prepare("<!doctype html><html><body>error</body></html>")
        self.assertEqual(self.output.read_text(encoding="utf-8"), original)

    def test_abnormal_count_drop_is_blocked(self) -> None:
        old_rules = [
            updater.Rule("HOST-SUFFIX", f"old{index}.example")
            for index in range(20)
        ]
        self.output.write_text(
            updater.render_rule_file(old_rules, "2026-01-01 00:00:00 UTC"),
            encoding="utf-8",
        )
        with self.assertRaises(updater.SafetyError):
            self.prepare(yaml_source(8))

    def test_unchanged_body_keeps_timestamp_and_content(self) -> None:
        source = yaml_source(8)
        rules = updater.process_rules(updater.parse_upstream(source))
        old_content = updater.render_rule_file(
            rules,
            "2026-01-01 00:00:00 UTC",
        )
        self.output.write_text(old_content, encoding="utf-8")

        result = self.prepare(
            source,
            now=dt.datetime(2026, 7, 28, 12, 0, tzinfo=dt.timezone.utc),
        )

        self.assertFalse(result.body_changed)
        self.assertFalse(result.changed)
        self.assertEqual(result.updated_at, "2026-01-01 00:00:00 UTC")
        self.assertEqual(result.new_content, old_content)

    def test_manual_rule_survives_upstream_update(self) -> None:
        self.manual.write_text(
            "# TYPE,value,source\n"
            "HOST-SUFFIX,manual-bybit.example,official documentation\n",
            encoding="utf-8",
        )
        result = self.prepare(yaml_source(8))
        self.assertIn(
            updater.Rule("HOST-SUFFIX", "manual-bybit.example"),
            result.new_rules,
        )
        self.assertEqual(result.manual_count, 1)


if __name__ == "__main__":
    unittest.main()
