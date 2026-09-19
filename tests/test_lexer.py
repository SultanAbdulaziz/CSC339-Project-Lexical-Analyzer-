"""Regression tests for the browser-facing lexical-analyzer runtime."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / "src" / "lib"
sys.path.insert(0, str(LIB_DIR))

import lex_bridge  # noqa: E402
from regex_to_NFA import regex_to_postfix  # noqa: E402


class LexerRuntimeTests(unittest.TestCase):
    def build(self, pairs: list[tuple[str, str]]) -> dict:
        specs = [{"name": name, "regex": regex} for name, regex in pairs]
        result = json.loads(lex_bridge.build(json.dumps(specs)))
        self.assertTrue(result["ok"], result.get("error"))
        return result

    def scan(self, source: str) -> dict:
        return json.loads(lex_bridge.scan_text(source))

    def test_regex_precedence_and_concatenation(self):
        self.assertEqual(
            regex_to_postfix("a(b|c)*"),
            ["a", "b", "c", "|", "*", "."],
        )

    def test_required_unary_operators(self):
        self.build([("COMPOSITE", "(a|b)*c+d?")])
        self.assertTrue(self.scan("ababcccd")["ok"])
        self.assertTrue(self.scan("ccc")["ok"])

    def test_equal_length_match_uses_specification_priority(self):
        self.build([
            ("KW_IF", "if"),
            ("ID", "[A-Za-z][A-Za-z0-9_]*"),
        ])
        result = self.scan("if iff")
        self.assertEqual(
            [(token["lexeme"], token["token"]) for token in result["tokens"]],
            [("if", "KW_IF"), ("iff", "ID")],
        )

    def test_maximal_munch_prefers_longest_prefix(self):
        self.build([("EQ", "=="), ("ASSIGN", "=")])
        result = self.scan("===")
        self.assertEqual(
            [(token["lexeme"], token["token"]) for token in result["tokens"]],
            [("==", "EQ"), ("=", "ASSIGN")],
        )

    def test_line_and_column_tracking(self):
        self.build([("ID", "[A-Za-z][A-Za-z0-9_]*")])
        result = self.scan("alpha\n\tbeta")
        self.assertEqual(result["tokens"][0]["line"], 1)
        self.assertEqual(result["tokens"][0]["col"], 1)
        self.assertEqual(result["tokens"][1]["line"], 2)
        self.assertEqual(result["tokens"][1]["col"], 2)

    def test_invalid_character_reports_first_position(self):
        self.build([("ID", "[A-Za-z][A-Za-z0-9_]*")])
        result = self.scan("ok @")
        self.assertFalse(result["ok"])
        self.assertEqual(result["tokens"][0]["lexeme"], "ok")
        self.assertIn("line 1, col 4", result["error"])

    def test_dot_generators_return_graphviz_documents(self):
        self.build([("KW_IF", "if"), ("ID", "[A-Za-z][A-Za-z0-9_]*")])
        self.assertTrue(lex_bridge.nfa_dot("KW_IF", 80).startswith("digraph NFA"))
        self.assertTrue(lex_bridge.dfa_dot(100, True, None).startswith("digraph DFA"))

    def test_stepper_and_full_scan_emit_the_same_tokens(self):
        self.build([
            ("KW_IF", "if"),
            ("ID", "[A-Za-z][A-Za-z0-9_]*"),
            ("ASSIGN", "="),
            ("NUM", "[0-9]+"),
            ("SEMI", ";"),
        ])
        source = "if value = 12;"
        expected = self.scan(source)["tokens"]
        json.loads(lex_bridge.step_init(source))
        stepped = json.loads(lex_bridge.step_run_to_end())
        self.assertEqual(stepped["tokens"], expected)


if __name__ == "__main__":
    unittest.main()
