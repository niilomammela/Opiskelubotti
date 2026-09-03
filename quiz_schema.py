"""Loading and validation for quiz JSON files."""

import json
from pathlib import Path


class QuizFormatError(ValueError):
    pass


def _require(cond, message):
    if not cond:
        raise QuizFormatError(message)


def _validate_option(option, q_id):
    _require(isinstance(option, dict), f"{q_id}: each option must be an object")
    _require("id" in option and "text" in option and "correct" in option,
              f"{q_id}: option missing 'id', 'text', or 'correct'")
    _require(isinstance(option["correct"], bool), f"{q_id}: option 'correct' must be true/false")


def _validate_question(q, index):
    q_id = q.get("id", f"question #{index + 1}")
    _require(isinstance(q, dict), f"question #{index + 1} must be an object")
    for field in ("id", "question", "type", "options"):
        _require(field in q, f"{q_id}: missing required field '{field}'")

    _require(q["type"] in ("single", "multiple"), f"{q_id}: type must be 'single' or 'multiple'")

    options = q["options"]
    _require(isinstance(options, list) and 3 <= len(options) <= 5,
              f"{q_id}: must have between 3 and 5 options")

    for opt in options:
        _validate_option(opt, q_id)

    correct_count = sum(1 for opt in options if opt["correct"])
    _require(correct_count >= 1, f"{q_id}: at least one option must be correct")
    if q["type"] == "single":
        _require(correct_count == 1, f"{q_id}: type is 'single' but {correct_count} options are marked correct")
    else:
        _require(correct_count >= 2, f"{q_id}: type is 'multiple' but only {correct_count} option is marked correct")

    q.setdefault("image", None)
    q.setdefault("explanation", "")


def load_quiz(path):
    """Parse and validate a quiz JSON file, returning the quiz dict.

    Raises QuizFormatError with a human-readable message on any problem.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise QuizFormatError(f"Could not read {path}: {exc}") from exc

    try:
        quiz = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise QuizFormatError(f"{path.name} is not valid JSON: {exc}") from exc

    _require(isinstance(quiz, dict), "Quiz file must contain a single JSON object")
    for field in ("title", "questions"):
        _require(field in quiz, f"Quiz file missing required field '{field}'")

    quiz.setdefault("subject", "")

    questions = quiz["questions"]
    _require(isinstance(questions, list) and len(questions) > 0, "Quiz must contain a non-empty 'questions' list")

    for i, q in enumerate(questions):
        _validate_question(q, i)

    return quiz


def list_quiz_files(quizzes_dir):
    """Return sorted list of .json Paths in the given directory."""
    quizzes_dir = Path(quizzes_dir)
    if not quizzes_dir.exists():
        return []
    return sorted(quizzes_dir.glob("*.json"))
