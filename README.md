# OpettajaBotti

Turn your course slide decks into self-study quizzes: Claude generates the questions, this Streamlit app plays them.

## Quickstart

```bash
# one-time setup
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# run the app
.venv/bin/streamlit run app.py
```

Open the URL Streamlit prints (defaults to http://localhost:8501). A sample quiz (`quizzes/example_quiz.json`) is included so you can try it immediately.

## Adding your own quiz

1. Open `MASTER_PROMPT.md`, copy its contents into a new Claude conversation, then paste or attach your slide deck.
2. Claude replies with a single JSON object containing the quiz.
3. Save that JSON as a new file in `quizzes/`, e.g. `quizzes/cell_biology.json`.
4. If the quiz needs images, export the slide figures Claude referenced and save them into `quizzes/images/` under the exact filenames it gave you.
5. Reload the app — your new quiz appears in the dropdown.

## Project layout

```
OpettajaBotti/
├── MASTER_PROMPT.md   # prompt you give Claude to turn slides into quiz JSON
├── app.py             # the Streamlit quiz app
├── quiz_schema.py     # quiz JSON loader/validator
├── requirements.txt
└── quizzes/
    ├── example_quiz.json
    └── images/         # images referenced by quiz questions/options
```

## Quiz file format

Each quiz is one JSON file. `quizzes/example_quiz.json` is a working example; `MASTER_PROMPT.md` contains the full schema. The essentials:

| Field | Meaning |
|---|---|
| `type` | `"single"` = exactly one correct option (shown as radio buttons). `"multiple"` = two or more correct options (shown as checkboxes). |
| `options` | List of `{id, text, correct}`. Order in the file doesn't matter — the app reshuffles options at runtime using true OS-level randomness (`random.SystemRandom`), not whatever order Claude wrote them in. |
| `image` | Optional filename under `quizzes/images/`, on a question or an individual option. |
| `explanation` | Shown to the student right after they submit an answer. |

## Behavior notes

- Feedback is immediate: each question is marked correct/incorrect with its explanation before you move on, and a final screen shows your score plus every question you missed.
- If a quiz file is malformed (e.g. Claude's JSON wasn't quite valid), the app shows a clear validation error in the quiz picker instead of crashing.
