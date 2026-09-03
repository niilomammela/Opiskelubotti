"""OpettajaBotti — quiz app for course slide decks."""

import copy
import random
from pathlib import Path

import streamlit as st

from latex_support import normalize_latex
from quiz_schema import QuizFormatError, list_quiz_files, load_quiz

BASE_DIR = Path(__file__).parent
QUIZZES_DIR = BASE_DIR / "quizzes"

st.set_page_config(page_title="OpettajaBotti", page_icon="📝", layout="centered")

# Question text is rendered as plain markdown rather than with st.subheader, so that
# display math ($$...$$) keeps its own line instead of being squeezed into a heading.
# This CSS gives those markdown blocks the weight a heading would have had.
TEXT_CSS = """
<style>
.st-key-question_text p { font-size: 1.3rem; font-weight: 600; margin-bottom: 0.25rem; }
.st-key-question_text .katex { font-size: 1.15em; }
[class*="st-key-review_q_"] p { font-weight: 600; }
/* KaTeX defaults to a smaller size than the surrounding widget label text. */
[data-testid="stRadio"] .katex, [data-testid="stCheckbox"] .katex { font-size: 1.1em; }
</style>
"""


def resolve_image(image_name):
    if not image_name:
        return None
    path = QUIZZES_DIR / "images" / image_name
    return str(path) if path.exists() else None


def shuffle_quiz(quiz):
    """Return a deep copy of the quiz with each question's options truly randomly shuffled."""
    shuffled = copy.deepcopy(quiz)
    rng = random.SystemRandom()
    for q in shuffled["questions"]:
        rng.shuffle(q["options"])
    return shuffled


def start_quiz(quiz_path):
    quiz = load_quiz(quiz_path)
    st.session_state.quiz = shuffle_quiz(quiz)
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.missed = []
    st.session_state.last_selection = None


def reset_to_picker():
    for key in ("quiz", "q_index", "score", "answered", "missed", "last_selection"):
        st.session_state.pop(key, None)


def render_picker():
    st.title("📝 OpettajaBotti")
    st.caption("Pick a quiz to study.")

    files = list_quiz_files(QUIZZES_DIR)
    if not files:
        st.warning(f"No quiz files found in `{QUIZZES_DIR}`. Add a `.json` quiz file there to get started.")
        return

    labels = {}
    for f in files:
        try:
            quiz = load_quiz(f)
            labels[f"{quiz['title']} ({len(quiz['questions'])} questions)"] = f
        except QuizFormatError as exc:
            labels[f"⚠️ {f.name} — invalid: {exc}"] = None

    choice = st.selectbox("Available quizzes", list(labels.keys()))
    selected_path = labels[choice]

    if selected_path is None:
        st.error("This quiz file has a format error and can't be loaded. Fix the JSON and reload the page.")
        return

    if st.button("Start quiz", type="primary"):
        start_quiz(selected_path)
        st.rerun()


def render_question():
    quiz = st.session_state.quiz
    questions = quiz["questions"]
    idx = st.session_state.q_index
    q = questions[idx]

    st.title(quiz["title"])
    st.progress((idx) / len(questions))
    st.caption(f"Question {idx + 1} of {len(questions)}  ·  Score: {st.session_state.score}/{idx}")

    with st.container(key="question_text"):
        st.markdown(normalize_latex(q["question"]))

    img_path = resolve_image(q.get("image"))
    if img_path:
        st.image(img_path)

    # Options are addressed by position so that two options rendering to the same
    # label (or to LaTeX that renders identically) stay distinguishable.
    def option_label(i):
        return normalize_latex(q["options"][i]["text"])

    if not st.session_state.answered:
        if q["type"] == "single":
            picked = st.radio(
                "Select one answer:",
                list(range(len(q["options"]))),
                format_func=option_label,
                index=None,
                key=f"radio_{idx}",
            )
            selected_ids = [q["options"][picked]["id"]] if picked is not None else []
        else:
            st.write("Select all that apply:")
            selected_ids = []
            for i, opt in enumerate(q["options"]):
                checked = st.checkbox(option_label(i), key=f"chk_{idx}_{opt['id']}")
                if checked:
                    selected_ids.append(opt["id"])

        submit_disabled = len(selected_ids) == 0
        if st.button("Submit answer", type="primary", disabled=submit_disabled):
            correct_ids = {opt["id"] for opt in q["options"] if opt["correct"]}
            is_correct = set(selected_ids) == correct_ids
            st.session_state.answered = True
            st.session_state.last_selection = set(selected_ids)
            if is_correct:
                st.session_state.score += 1
            else:
                st.session_state.missed.append({
                    "question": q["question"],
                    "correct_texts": [opt["text"] for opt in q["options"] if opt["correct"]],
                })
            st.rerun()
    else:
        selected_ids = st.session_state.last_selection
        correct_ids = {opt["id"] for opt in q["options"] if opt["correct"]}
        is_correct = selected_ids == correct_ids

        for opt in q["options"]:
            marker = "⚪" if q["type"] == "single" else "⬜"
            if opt["correct"]:
                marker = "🟢" if q["type"] == "single" else "🟩"
            elif opt["id"] in selected_ids:
                marker = "🔴" if q["type"] == "single" else "🟥"
            st.markdown(f"{marker} {normalize_latex(opt['text'])}")

        if is_correct:
            st.success("Correct!")
        else:
            st.error("Not quite.")

        if q.get("explanation"):
            st.info(normalize_latex(q["explanation"]))

        is_last = idx == len(questions) - 1
        if st.button("See results" if is_last else "Next question", type="primary"):
            st.session_state.q_index += 1
            st.session_state.answered = False
            st.session_state.last_selection = None
            st.rerun()


def render_summary():
    quiz = st.session_state.quiz
    total = len(quiz["questions"])
    score = st.session_state.score

    st.title("Quiz complete!")
    st.subheader(f"Score: {score}/{total}")
    st.progress(score / total if total else 0)

    if st.session_state.missed:
        st.write("### Questions to review")
        for i, item in enumerate(st.session_state.missed):
            with st.container(key=f"review_q_{i}"):
                st.markdown(normalize_latex(item["question"]))
            st.markdown("Correct answer(s): " + ", ".join(
                normalize_latex(text) for text in item["correct_texts"]))
            st.divider()
    else:
        st.balloons()
        st.write("Perfect score!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Retake this quiz"):
            quiz_title = quiz["title"]
            path = next((f for f in list_quiz_files(QUIZZES_DIR)
                         if load_quiz(f)["title"] == quiz_title), None)
            reset_to_picker()
            if path:
                start_quiz(path)
            st.rerun()
    with col2:
        if st.button("Choose another quiz"):
            reset_to_picker()
            st.rerun()


def main():
    st.markdown(TEXT_CSS, unsafe_allow_html=True)

    if "quiz" not in st.session_state:
        render_picker()
        return

    quiz = st.session_state.quiz
    if st.session_state.q_index >= len(quiz["questions"]):
        render_summary()
    else:
        render_question()


if __name__ == "__main__":
    main()
