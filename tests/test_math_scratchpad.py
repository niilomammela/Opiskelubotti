"""Tests for the embedded formula-editor scratchpad."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from math_scratchpad import MATHLIVE_BASE, MATHLIVE_URL, build_editor_html, storage_key


class StorageKeyTest(unittest.TestCase):
    def test_key_includes_the_session_id(self):
        self.assertIn("abc123", storage_key("abc123"))

    def test_different_sessions_get_different_keys(self):
        self.assertNotEqual(storage_key("one"), storage_key("two"))


class EditorHtmlTest(unittest.TestCase):
    def test_loads_the_pinned_editor(self):
        html = build_editor_html("s1")
        self.assertIn(MATHLIVE_URL, html)
        # A pinned version, not a floating tag that could change under the student.
        self.assertRegex(MATHLIVE_URL, r"mathlive@\d+\.\d+\.\d+/")

    def test_renders_math_field_elements(self):
        html = build_editor_html("s1")
        self.assertIn("math-field", html)
        self.assertIn("customElements.get('math-field')", html)

    def test_points_mathlive_at_its_own_font_directory(self):
        # Left unset, MathLive resolves fonts against the host page rather than
        # the CDN script, and every glyph silently 404s.
        html = build_editor_html("s1")
        self.assertIn("fontsDirectory", html)
        self.assertIn(MATHLIVE_BASE + "/fonts", html)

    def test_no_leftover_template_placeholders(self):
        self.assertIsNone(re.search(r"__[A-Z_]+__", build_editor_html("s1")))

    def test_embeds_the_session_specific_storage_key(self):
        html = build_editor_html("s1")
        self.assertIn(storage_key("s1"), html)
        self.assertNotIn(storage_key("s2"), html)

    def test_session_id_is_escaped_into_the_script(self):
        # A hostile id must not be able to close the string literal or the tag.
        html = build_editor_html('x" ;</script><script>alert(1)//')
        self.assertNotIn("<script>alert(1)", html)

    def test_does_not_bind_reserved_window_properties(self):
        # `var status = <element>` silently coerces to a string, because
        # window.status is a legacy DOMString in the HTML spec — the element
        # method calls on it then throw.
        html = build_editor_html("s1")
        for reserved in ("status", "name", "length", "top", "self"):
            self.assertNotRegex(html, rf"\b(var|let|const)\s+{reserved}\b")

    def test_declares_an_explicit_light_color_scheme(self):
        # Without this the iframe inherits Streamlit's dark scheme and the
        # editor's dark-on-white text becomes unreadable.
        html = build_editor_html("s1")
        self.assertIn("color-scheme: light", html)

    def test_virtual_keyboard_is_opened_only_on_request(self):
        # An automatic keyboard covers the working area in a panel this short.
        html = build_editor_html("s1")
        self.assertIn("math-virtual-keyboard-policy", html)
        self.assertIn("manual", html)

    def test_pins_mathlive_to_its_light_palette(self):
        # MathLive picks its palette from @media (prefers-color-scheme: dark)
        # alone, which `color-scheme: light` does not influence. On a dark-mode
        # machine it would otherwise paint dark-theme highlights and selection
        # colours onto this deliberately white sheet.
        html = build_editor_html("s1")
        self.assertIn("--contains-highlight-background-color: transparent", html)
        self.assertIn("--selection-background-color", html)

    def test_hosts_the_virtual_keyboard_inside_the_iframe(self):
        # In an iframe MathLive installs a proxy that postMessages the keyboard
        # to the top-level page, which in a Streamlit component is Streamlit
        # itself — it has no MathLive, so the button would do nothing.
        html = build_editor_html("s1")
        self.assertIn("initVirtualKeyboardInCurrentBrowsingContext", html)

    def test_keyboard_button_reports_when_it_cannot_work(self):
        # Silent no-op buttons are how the previous version hid this bug.
        html = build_editor_html("s1")
        self.assertIn("disabled", html)

    def test_shows_a_message_until_the_editor_loads(self):
        html = build_editor_html("s1")
        self.assertIn("Ladataan", html)
        self.assertIn("internet", html.lower())

    def test_storage_access_is_guarded(self):
        # sessionStorage throws outright in some sandboxed iframes; the editor
        # must still come up, just without remembering anything.
        html = build_editor_html("s1")
        self.assertGreaterEqual(len(re.findall(r"\bcatch\b", html)), 2)


if __name__ == "__main__":
    unittest.main()
