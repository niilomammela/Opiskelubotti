"""Embedded formula editor ("kaavaeditori") used as scrap paper while answering.

The editor is MathLive's `<math-field>` custom element: you type maths and see
it typeset as you go, with a symbol palette (MathLive's virtual keyboard) for
the notation that is awkward to type. The scratchpad stacks one field per line,
so a derivation can be worked down the page.

MathLive is a single self-contained script that is designed to be embedded, and
that is why it is used here rather than the editor from math-demo.abitti.fi:
that one assumes it owns the whole page (a fixed-position toolbar, a server
endpoint rendering `/math.svg?latex=...`, a stylesheet from a separate package,
and a React portal into a `display: contents` stub inside a contenteditable),
and inside a short Streamlit component iframe its formula popup never painted.

Everything typed here stays inside the component's iframe: nothing is sent back
to Python, scored, or written to disk. Content survives Streamlit reruns by way
of ``sessionStorage``, keyed per quiz run, so starting or retaking a quiz hands
the student a blank sheet.
"""

import json

import streamlit as st

# Pinned rather than floating on `latest`, so the editor cannot change under
# the student. The fonts and sounds live alongside it in the same CDN folder.
MATHLIVE_VERSION = "0.110.0"
MATHLIVE_BASE = f"https://cdn.jsdelivr.net/npm/mathlive@{MATHLIVE_VERSION}"
MATHLIVE_URL = f"{MATHLIVE_BASE}/mathlive.min.js"

# Room for several lines of working plus the symbol palette, which opens
# inside this panel and is about 230px tall.
EDITOR_HEIGHT = 620

# How long to wait for the CDN before telling the student it isn't coming.
_LOAD_TIMEOUT_MS = 15000

_STORAGE_PREFIX = "opettajabotti-scratchpad-"

_TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<style>
  /* The component iframe is transparent and inherits the host's colour
     scheme, so a dark Streamlit theme would show through the editor's
     dark-on-white text. Declare an explicitly light document. */
  :root { color-scheme: light; }
  html, body {
    margin: 0;
    background: #fff;
    color: #111;
    font-family: "Source Sans Pro", system-ui, sans-serif;
  }
  #bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid #e3e6e8;
  }
  #kbd {
    font: inherit;
    font-size: 0.9rem;
    padding: 0.25rem 0.7rem;
    border: 1px solid #c9ced2;
    border-radius: 0.35rem;
    background: #f6f7f8;
    color: #111;
    cursor: pointer;
  }
  #kbd:hover { background: #eceef0; }
  #hint { color: #55595e; font-size: 0.85rem; }
  #sheet { padding: 0.5rem 0.6rem; }
  /* Keep the working area clear of the keyboard when it is open. */
  body.kbd-open #sheet { padding-bottom: 240px; }
  math-field {
    /* MathLive chooses its palette from @media (prefers-color-scheme: dark)
       alone — `color-scheme: light` does not affect media queries — so on a
       dark-mode machine it paints dark-theme colours onto this white sheet.
       Pin the handful of colours that would otherwise clash. */
    --contains-highlight-background-color: transparent;
    --selection-background-color: hsl(200, 70%, 85%);
    --selection-color: #000;
    --caret-color: #111;
    --placeholder-color: #8a9096;
    display: block;
    width: 100%;
    margin: 0 0 0.4rem;
    padding: 0.35rem 0.5rem;
    border: 1px solid #d7dbde;
    border-radius: 0.35rem;
    background: #fff;
    color: #111;
    font-size: 1.15rem;
  }
  math-field:focus-within {
    border-color: #359bb7;
    outline: 1px solid #359bb7;
  }
  #status { padding: 0.75rem; color: #55595e; font-size: 0.9rem; }
</style>
<div id="status">Ladataan kaavaeditoria…</div>
<div id="bar" hidden>
  <button id="kbd" type="button">⌨ Symbolit</button>
  <span id="hint">Enter = uusi rivi · ^ = potenssi · / = jakolasku · \\\\sqrt = juuri</span>
</div>
<div id="sheet" hidden></div>
<script src="__MATHLIVE_URL__"></script>
<script>
(function () {
  'use strict';
  // Deliberately not named plainly: a top-level variable called "status"
  // writes to window.status, a legacy DOMString in the HTML spec, which
  // silently stringifies the element and breaks every method call on it.
  var statusEl = document.getElementById('status');
  var bar = document.getElementById('bar');
  var sheet = document.getElementById('sheet');
  var KEY = __STORAGE_KEY__;
  var DEADLINE = Date.now() + __TIMEOUT_MS__;
  // The keyboard sends its keystrokes to whichever field was last focused.
  var lastField = null;

  function loadSaved() {
    try {
      return JSON.parse(window.sessionStorage.getItem(KEY) || '[]');
    } catch (e) {
      return [];
    }
  }

  function save() {
    try {
      var rows = [].map.call(sheet.children, function (f) { return f.value; });
      window.sessionStorage.setItem(KEY, JSON.stringify(rows));
    } catch (e) {
      // Sandboxed without same-origin access: the editor still works, it just
      // forgets between reruns.
    }
  }

  function addRow(latex, after) {
    var field = document.createElement('math-field');
    // Keep the palette under the student's control; an automatic keyboard
    // would cover the working area in a panel this short.
    field.setAttribute('math-virtual-keyboard-policy', 'manual');
    field.addEventListener('input', save);
    field.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter') {
        ev.preventDefault();
        addRow('', field).focus();
      } else if (ev.key === 'Backspace' && field.value === '' && sheet.children.length > 1) {
        ev.preventDefault();
        var prev = field.previousElementSibling || field.nextElementSibling;
        field.remove();
        if (prev) prev.focus();
        save();
      }
    });
    if (after && after.nextSibling) {
      sheet.insertBefore(field, after.nextSibling);
    } else {
      sheet.appendChild(field);
    }
    // Assigning after insertion lets MathLive typeset immediately.
    field.value = latex || '';
    return field;
  }

  function setupKeyboard(ML) {
    var btn = document.getElementById('kbd');
    // Inside an iframe MathLive installs a proxy that postMessages the
    // keyboard to the top-level page. Here that page is the Streamlit app,
    // which has no MathLive to answer, so the keyboard never appears and the
    // button silently does nothing. This makes *this* frame host the real
    // keyboard instead of delegating it.
    if (typeof ML.initVirtualKeyboardInCurrentBrowsingContext === 'function') {
      ML.initVirtualKeyboardInCurrentBrowsingContext();
    }
    var kb = window.mathVirtualKeyboard;
    if (!kb || typeof kb.show !== 'function') {
      btn.disabled = true;
      btn.title = 'Symbolipaletti ei ole käytettävissä tässä selaimessa.';
      return;
    }
    btn.addEventListener('click', function () {
      // The keyboard types into whichever field has focus, and clicking the
      // button takes focus away from it.
      var target = lastField || sheet.firstElementChild;
      if (kb.visible) {
        kb.hide();
      } else {
        if (target) target.focus();
        kb.show();
      }
      btn.setAttribute('aria-pressed', kb.visible ? 'true' : 'false');
      document.body.classList.toggle('kbd-open', !!kb.visible);
    });
  }

  function init() {
    var ML = window.MathLive;
    // Without explicit directories MathLive resolves these against the host
    // page, not the CDN script, and the glyph fonts silently 404.
    ML.MathfieldElement.fontsDirectory = '__MATHLIVE_BASE__/fonts';
    ML.MathfieldElement.soundsDirectory = null;

    var saved = loadSaved();
    if (!saved.length) saved = [''];
    saved.forEach(function (latex) { addRow(latex); });

    sheet.addEventListener('focusin', function (ev) {
      if (ev.target.tagName === 'MATH-FIELD') lastField = ev.target;
    });

    setupKeyboard(ML);

    statusEl.remove();
    bar.hidden = false;
    sheet.hidden = false;
  }

  (function waitForMathLive() {
    if (window.MathLive && window.customElements.get('math-field')) {
      init();
      return;
    }
    if (Date.now() > DEADLINE) {
      statusEl.textContent =
        'Kaavaeditoria ei voitu ladata — se haetaan verkosta, joten tarvitset internet-yhteyden.';
      return;
    }
    setTimeout(waitForMathLive, 50);
  })();
})();
</script>
"""


def storage_key(session_id):
    """The ``sessionStorage`` key holding this quiz run's scratchpad content."""
    return f"{_STORAGE_PREFIX}{session_id}"


def build_editor_html(session_id):
    """Return the standalone HTML document that hosts the formula editor."""
    # json.dumps gives a JS string literal with quotes and backslashes escaped;
    # escaping '<' as well keeps a hostile id from closing the <script> tag.
    key_literal = json.dumps(storage_key(session_id)).replace("<", "\\u003c")
    return (
        _TEMPLATE
        .replace("__MATHLIVE_URL__", MATHLIVE_URL)
        .replace("__MATHLIVE_BASE__", MATHLIVE_BASE)
        .replace("__STORAGE_KEY__", key_literal)
        .replace("__TIMEOUT_MS__", str(_LOAD_TIMEOUT_MS))
    )


def render_scratchpad(session_id):
    """Render the collapsed formula-editor expander."""
    with st.expander("🧮 Kaavaeditori", expanded=False):
        st.caption(
            "Laskupaperi tehtävän ratkomiseen — sisältöä ei tallenneta eikä tarkasteta."
        )
        # st.iframe embeds the HTML with same-origin access, which is what lets
        # the editor reach sessionStorage to survive a rerun.
        st.iframe(build_editor_html(session_id), height=EDITOR_HEIGHT)
