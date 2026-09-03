# OpettajaBotti

A small Streamlit app for turning course slide decks into self-study quizzes.

## How it works

1. Copy the prompt from `MASTER_PROMPT.md` into a Claude conversation, then paste/attach your slide deck.
2. Claude outputs a quiz as a single JSON object.
3. Save that JSON as a new file in `quizzes/` (e.g. `quizzes/cell_biology.json`).
4. If the quiz references images, export the corresponding slide figures and save them into `quizzes/images/` under the filenames Claude specified.
5. Run the app and pick your quiz from the dropdown.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/streamlit run app.py
```

Then open the URL Streamlit prints (defaults to http://localhost:8501).

## Project layout

```
OpettajaBotti/
├── MASTER_PROMPT.md   # copy-paste prompt for Claude to generate quiz JSON from slides
├── app.py             # the Streamlit quiz app
├── quiz_schema.py      # quiz JSON loader/validator
├── latex_support.py   # normalizes LaTeX delimiters for rendering
├── requirements.txt
├── tests/             # unit tests (`.venv/bin/python -m unittest discover -s tests`)
└── quizzes/
    ├── example_quiz.json
    ├── example_latex_quiz.json
    └── images/         # images referenced by quiz questions/options
```

## Quiz file format

Each quiz is a single JSON file. See `quizzes/example_quiz.json` for a working example, and `MASTER_PROMPT.md` for the full schema definition. Key points:

- `type` is `"single"` (exactly one correct option, shown as radio buttons) or `"multiple"` (two or more correct options, shown as checkboxes).
- Option order in the file doesn't matter — the app shuffles options at runtime using true OS-level randomness (`random.SystemRandom`), not whatever order Claude wrote them in.
- `image` fields (on a question or an option) point to a filename under `quizzes/images/`.
- `explanation` is shown to the student after they submit an answer.
- Question text, option text, and explanations may contain LaTeX — see below.

## LaTeX formulas

Any quiz text (question, option, explanation, review list) can contain LaTeX, which the
app renders with KaTeX:

- `$...$` for inline math: `"The thermal voltage $U_T$ is ~26 mV"`
- `$$...$$` for display math on its own line: `"$$I_D = I_S(e^{U_D/(nU_T)} - 1)$$"`
- `\(...\)` and `\[...\]` also work — the app converts them to the `$` forms.
- A lone `$` that isn't part of a formula is escaped automatically and displays literally,
  so prices like "costs $5" don't accidentally start a formula.

Because quizzes are JSON, backslashes must be doubled in the file: `\\frac{a}{b}` in the
JSON renders as the fraction. See `quizzes/example_latex_quiz.json` for a working example.

## Notes

- Each quiz is scored with immediate per-question feedback (correct/incorrect + explanation), then a final score summary with a list of missed questions.
- Tests live in `tests/` and run with `.venv/bin/python -m unittest discover -s tests`.
- A malformed quiz JSON file shows a clear validation error in the app's quiz picker instead of crashing.
