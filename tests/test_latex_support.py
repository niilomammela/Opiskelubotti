"""Tests for the LaTeX normalization used when rendering quiz text."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from latex_support import has_latex, normalize_latex


class NormalizeLatexTest(unittest.TestCase):
    def test_empty_and_missing_text(self):
        self.assertEqual(normalize_latex(""), "")
        self.assertEqual(normalize_latex(None), "")

    def test_plain_text_is_untouched(self):
        self.assertEqual(normalize_latex("What is a pn junction?"), "What is a pn junction?")

    def test_existing_dollar_math_is_untouched(self):
        self.assertEqual(normalize_latex("The current $I_D$ grows."), "The current $I_D$ grows.")
        self.assertEqual(normalize_latex("$$E = mc^2$$"), "$$E = mc^2$$")

    def test_paren_delimiters_become_inline_math(self):
        self.assertEqual(normalize_latex(r"Given \(x^2 + 1\) it holds."), "Given $x^2 + 1$ it holds.")

    def test_bracket_delimiters_become_display_math(self):
        self.assertEqual(normalize_latex(r"\[\int_0^1 x\,dx\]"), r"$$\int_0^1 x\,dx$$")

    def test_multiple_spans_in_one_string(self):
        self.assertEqual(
            normalize_latex(r"\(a\) and \(b\) differ"),
            "$a$ and $b$ differ",
        )

    def test_multiline_display_math(self):
        self.assertEqual(normalize_latex("\\[a\n+ b\\]"), "$$a\n+ b$$")

    def test_stray_dollar_is_escaped(self):
        self.assertEqual(normalize_latex("A diode costs $5 today"), r"A diode costs \$5 today")

    def test_stray_dollar_alongside_real_math(self):
        self.assertEqual(
            normalize_latex("$V_T$ costs $5"),
            r"$V_T$ costs \$5",
        )

    def test_already_escaped_dollar_is_left_alone(self):
        self.assertEqual(normalize_latex(r"costs \$5"), r"costs \$5")

    def test_display_math_wins_over_inline_pairing(self):
        self.assertEqual(normalize_latex("$$a + b$$ and $c$"), "$$a + b$$ and $c$")


class HasLatexTest(unittest.TestCase):
    def test_detects_dollar_math(self):
        self.assertTrue(has_latex("value $x$"))

    def test_detects_paren_math(self):
        self.assertTrue(has_latex(r"value \(x\)"))

    def test_plain_text_has_no_latex(self):
        self.assertFalse(has_latex("value x"))
        self.assertFalse(has_latex("costs $5"))
        self.assertFalse(has_latex(""))


if __name__ == "__main__":
    unittest.main()
