"""Helpers for rendering quiz text that contains LaTeX formulas.

Streamlit's markdown renderer (KaTeX) understands ``$...$`` for inline math and
``$$...$$`` for display math. Quiz authors — including Claude, which writes most
of these files — routinely use the other common delimiters ``\\(...\\)`` and
``\\[...\\]`` instead, and sometimes write a stray dollar sign that is meant as
currency. :func:`normalize_latex` bridges both gaps so quiz JSON renders the way
its author intended.
"""

import re

# \( ... \) and \[ ... \] as written inside a JSON string.
_INLINE_DELIMS = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
_DISPLAY_DELIMS = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)

# A complete math span: $$...$$ first, so it wins over the inline pattern.
_MATH_SPAN = re.compile(r"(?<!\\)\$\$.+?(?<!\\)\$\$|(?<!\\)\$.+?(?<!\\)\$", re.DOTALL)

_UNESCAPED_DOLLAR = re.compile(r"(?<!\\)\$")


def _convert_delimiters(text):
    text = _DISPLAY_DELIMS.sub(r"$$\1$$", text)
    return _INLINE_DELIMS.sub(r"$\1$", text)


def _escape_stray_dollars(text):
    """Escape any ``$`` that is not part of a matched math span.

    Without this, a single dollar sign somewhere in the text opens a math span
    that never closes, and KaTeX swallows the rest of the paragraph.
    """
    out = []
    cursor = 0
    for span in _MATH_SPAN.finditer(text):
        out.append(_UNESCAPED_DOLLAR.sub(r"\\$", text[cursor:span.start()]))
        out.append(span.group(0))
        cursor = span.end()
    out.append(_UNESCAPED_DOLLAR.sub(r"\\$", text[cursor:]))
    return "".join(out)


def normalize_latex(text):
    """Return `text` with its math delimiters normalized for Streamlit.

    Converts ``\\(...\\)`` to ``$...$`` and ``\\[...\\]`` to ``$$...$$``, leaves
    existing ``$``/``$$`` spans untouched, and escapes leftover dollar signs so
    they display literally. Returns ``""`` for empty/missing text.
    """
    if not text:
        return ""
    return _escape_stray_dollars(_convert_delimiters(text))


def has_latex(text):
    """True if `text` contains at least one complete math span."""
    if not text:
        return False
    return _MATH_SPAN.search(_convert_delimiters(text)) is not None
