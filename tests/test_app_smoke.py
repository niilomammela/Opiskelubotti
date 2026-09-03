"""Smoke test: drive the Streamlit app through a LaTeX quiz with AppTest."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest


class AppSmokeTest(unittest.TestCase):
    def _run_latex_quiz(self):
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        at.selectbox[0].select("Example Quiz: Formulas with LaTeX (4 questions)").run()
        at.button[0].click().run()
        return at

    def test_first_question_renders_latex_markdown(self):
        at = self._run_latex_quiz()
        self.assertFalse(at.exception)
        body = " ".join(m.value for m in at.markdown)
        self.assertIn("$", body)

    def test_option_labels_are_latex_normalized(self):
        at = self._run_latex_quiz()
        labels = list(at.radio[0].options)
        self.assertTrue(any("$" in label for label in labels))
        self.assertFalse(any(chr(92) + "(" in label for label in labels))

    def test_answering_a_question_shows_feedback(self):
        at = self._run_latex_quiz()
        at.radio[0].set_value(0).run()
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertTrue(at.success or at.error)
        self.assertTrue(at.info)


if __name__ == "__main__":
    unittest.main()
