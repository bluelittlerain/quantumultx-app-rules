from __future__ import annotations

import re
import unittest
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
RULE_ROOT = ROOT / "rule" / "QuantumultX"


@dataclass(frozen=True)
class AppEntry:
    display_name: str
    directory: str
    main_rule: Path


def _available_rules_block(text: str) -> str:
    match = re.search(
        r"(?ms)^## Available Rules\s*$\n(?P<body>.*?)(?=^##\s|\Z)", text
    )
    if not match:
        raise AssertionError("README is missing a parseable '## Available Rules' section")
    return match.group("body")


def _local_rule_path(target: str) -> Path:
    parsed = urllib.parse.urlsplit(target)
    source_path = urllib.parse.unquote(parsed.path if parsed.scheme else target)
    marker = "/rule/QuantumultX/"
    normalized = source_path.replace("\\", "/")
    if marker in normalized:
        normalized = "rule/QuantumultX/" + normalized.split(marker, 1)[1]
    normalized = normalized.lstrip("/")
    return Path(*normalized.split("/"))


def parse_available_rules(text: str) -> list[AppEntry]:
    block = _available_rules_block(text)
    sections = list(
        re.finditer(
            r"(?ms)^### (?P<name>[^\r\n]+?)\s*$\n"
            r"(?P<body>.*?)(?=^### |\Z)",
            block,
        )
    )
    if not sections:
        raise AssertionError("Available Rules contains no application headings")

    entries: list[AppEntry] = []
    for section in sections:
        display_name = section.group("name").strip()
        body = section.group("body")
        directory_match = re.search(
            r"(?m)^- 目录：\[[^\]]+\]\(rule/QuantumultX/([^/)]+)/\)\s*$",
            body,
        )
        if not directory_match:
            raise AssertionError(f"{display_name}: missing canonical directory link")
        directory = directory_match.group(1)

        main_match = re.search(
            r"(?m)^- 主规则：\[[^\]]+\]\(([^)]+)\)", body
        )
        if not main_match:
            raise AssertionError(f"{display_name}: missing main rule link")
        main_rule = _local_rule_path(main_match.group(1).strip())
        entries.append(AppEntry(display_name, directory, main_rule))
    return entries


def parse_intro_names(text: str) -> list[str]:
    preamble = text.split("## Available Rules", 1)[0]
    match = re.search(r"(?m)^当前提供 (.+?) 等独立规则。\s*$", preamble)
    if not match:
        raise AssertionError("README is missing the canonical current-app introduction")
    return [
        item.strip()
        for item in re.split(r"、|\s+和\s+", match.group(1))
        if item.strip()
    ]


class RootReadmeAppOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = README.read_text(encoding="utf-8")
        cls.entries = parse_available_rules(cls.text)

    def test_available_rules_are_casefold_sorted(self) -> None:
        names = [entry.display_name for entry in self.entries]
        self.assertEqual(names, sorted(names, key=str.casefold))

    def test_available_rules_are_unique(self) -> None:
        folded = [entry.display_name.casefold() for entry in self.entries]
        self.assertEqual(len(folded), len(set(folded)))

    def test_directories_and_main_rules_exist(self) -> None:
        for entry in self.entries:
            with self.subTest(app=entry.display_name):
                directory = RULE_ROOT / entry.directory
                expected_main = (
                    Path("rule")
                    / "QuantumultX"
                    / entry.directory
                    / f"{entry.directory}.list"
                )
                self.assertTrue(directory.is_dir(), f"missing directory: {directory}")
                self.assertEqual(entry.main_rule, expected_main)
                self.assertTrue(
                    (ROOT / entry.main_rule).is_file(),
                    f"missing main rule: {entry.main_rule.as_posix()}",
                )

    def test_all_formal_rule_directories_are_listed(self) -> None:
        formal_directories = {
            path.name
            for path in RULE_ROOT.iterdir()
            if path.is_dir()
            and (path / "README.md").is_file()
            and (path / f"{path.name}.list").is_file()
        }
        listed_directories = {entry.directory for entry in self.entries}
        self.assertEqual(listed_directories, formal_directories)

    def test_wirex_one_is_listed(self) -> None:
        names = [entry.display_name for entry in self.entries]
        self.assertIn("Wirex One", names)

    def test_intro_order_matches_available_rules(self) -> None:
        names = [entry.display_name for entry in self.entries]
        self.assertEqual(parse_intro_names(self.text), names)


if __name__ == "__main__":
    unittest.main()
