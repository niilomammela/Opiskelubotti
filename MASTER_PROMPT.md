# Master Prompt — Slide Deck → Quiz JSON

Copy everything in the box below into Claude, then attach/paste your slide deck content (text export, PDF, or images of the slides). Optionally tell Claude the desired number of questions; otherwise it will pick a reasonable number based on how much material there is (roughly 1 question per substantial slide/concept, skipping title/agenda/reference slides).

---

```
You are generating a quiz file for a self-study quiz app from a university course slide deck. Follow every rule below exactly.

## Your task
1. Read through the slides I provide and identify the important, testable concepts — definitions, mechanisms, relationships, comparisons, processes, cause/effect, and key facts a student should know after this lecture. Skip trivial content (title slides, agendas, "questions?" slides, pure references/citations) and skip overly obscure details that are not the point of the lecture.
2. Write one quiz question per concept (unless I told you a specific number of questions — if so, prioritize the most important concepts to hit that count).
3. Output ONLY a single JSON object matching the schema below. No markdown code fences, no commentary before or after, no explanations outside the JSON — just the raw JSON object.

## Question design rules (this is the part that matters most)
- **Diversity of question types.** Do not make every question "which of the following is X". Vary across: definitions ("What is X?"), comparisons ("How does X differ from Y?"), cause/effect ("What happens if X?"), application/scenario ("A student observes X — which concept explains this?"), process/ordering, and "select all that apply" style. Avoid repeating the same sentence template back-to-back.
- **Mix single-answer and multiple-answer questions.** Roughly 60-70% single-correct-answer, 30-40% multiple-correct-answer (more than one right option). Multiple-answer questions should have at least 2 correct options among the choices.
- **Believable distractors.** Wrong options must be plausible: same category and granularity as the correct answer, drawn from real adjacent concepts in the material or common student misconceptions — not absurd, off-topic, or obviously-wrong filler. Never use "All of the above" / "None of the above" as an option. Aim for 4 options per question (minimum 3, maximum 5).
- **No order signals.** Write the options in whatever order occurs to you — do NOT try to manually randomize or shuffle them yourself, and do NOT put the correct answer in a "safe" middle position out of habit. The app that displays these questions will re-shuffle the option order itself using true randomness, so your ordering is discarded anyway. Just focus on writing good options; order does not matter.
- **Explanations.** For every question, write a 1-2 sentence `explanation` that clarifies why the correct option(s) are correct and, where useful, why a common wrong option is wrong. This is shown to the student after they answer.
- **Images.** If I have separately given you slide images and a question specifically depends on a diagram/figure that can't be understood from text alone, set the question's `image` field to a filename you invent in the form `q<N>.png` (e.g. `q3.png`) and separately tell me, after the JSON, which original slide/figure that filename corresponds to so I can export and save it as `quizzes/images/q<N>.png`. If no image is needed, set `image` to `null`. Do not invent images for questions that don't need one.

## Output JSON schema (follow field names and types exactly)

{
  "title": "<short quiz title, e.g. the lecture/topic name>",
  "subject": "<course or subject name>",
  "questions": [
    {
      "id": "q1",
      "question": "<the question text>",
      "image": null,
      "type": "single",
      "options": [
        {"id": "a", "text": "<option text>", "correct": true},
        {"id": "b", "text": "<option text>", "correct": false},
        {"id": "c", "text": "<option text>", "correct": false},
        {"id": "d", "text": "<option text>", "correct": false}
      ],
      "explanation": "<why the correct answer is correct>"
    }
  ]
}

Field rules:
- `id` fields: unique per question (q1, q2, ...) and per option within a question (a, b, c, d...).
- `type`: must be exactly `"single"` if exactly one option has `"correct": true`, or `"multiple"` if two or more options have `"correct": true`. Never have zero correct options.
- `image`: `null`, or a relative filename like `"q3.png"` as described above. Options may also optionally carry their own `"image"` field the same way, if a question is "which image shows X" style — only use this if genuinely useful.
- `options`: at least 3, at most 5 entries.
- `explanation`: always present, 1-2 sentences.

Now here are the slides:
```

---

## Notes for you (not part of the prompt)
- After Claude replies, save the JSON it outputs as a new file in `quizzes/`, e.g. `quizzes/cell_biology_mitochondria.json`.
- If Claude mentions needing images, export those slide figures and save them into `quizzes/images/` under the exact filenames it specified.
- If Claude ever wraps the JSON in ```json fences or adds stray text, just strip that out before saving — the app expects a plain `.json` file containing only the JSON object.
- If you want more or fewer questions, add a line before "Now here are the slides:" such as: `Generate exactly 12 questions.`
