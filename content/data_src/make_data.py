#!/usr/bin/env python3
"""Write data/bank.js, data/exam.js and data/flashcards.js from the lists in this folder.

    python content/data_src/make_data.py

Also checks every question: a valid answer index, no duplicate options, and a known topic.
build.py runs this first, so a plain `python build.py` is enough.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from bank import BANK  # noqa: E402
from cards import CARDS  # noqa: E402
from exam import EXAM  # noqa: E402

TOPICS = ["concepts", "method", "sendrecv", "collectives", "trapezoid", "odd_even", "heat",
          "performance", "gpgpu", "imaging", "filters"]
KINDS = {"concept", "scenario", "calc"}


def check(qs, label):
    for i, q in enumerate(qs):
        where = f"{label} #{i + 1} ({q['q'][:50]})"
        assert q["topic"] in TOPICS, f"{where}: unknown topic {q['topic']}"
        assert q["kind"] in KINDS, f"{where}: unknown kind {q['kind']}"
        n = len(q["options"])
        assert len(set(q["options"])) == n, f"{where}: duplicate options"
        ans = q["answer"] if isinstance(q["answer"], list) else [q["answer"]]
        assert ans and all(0 <= a < n for a in ans), f"{where}: bad answer {q['answer']}"


def clean(q, qid):
    out = {"id": qid, "topic": q["topic"], "kind": q["kind"], "q": q["q"]}
    for k in ("ctx", "code"):
        if q.get(k):
            out[k] = q[k]
    out.update(options=q["options"], answer=q["answer"], why=q["why"])
    return out


def main():
    check(BANK, "bank")
    check(EXAM, "exam")
    seen = {}
    rows = []
    for q in BANK:
        seen[q["topic"]] = seen.get(q["topic"], 0) + 1
        rows.append(clean(q, f"b-{q['topic']}-{seen[q['topic']]}"))
    (ROOT / "data" / "bank.js").write_text(
        "/* Topic quiz bank. Generated from content/data_src/bank.py: edit there, then run build.py.\n"
        "   Each question: { id, topic, kind: 'concept'|'scenario'|'calc', q, code?, ctx?, options[], answer, why }.\n"
        "   answer is an option index, or an array of indices for \"select all that apply\". Options are shuffled when shown. */\n"
        "window.QUIZ_BANK = [\n" + ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in rows) + "\n];\n",
        encoding="utf-8")
    rows = [clean(q, f"e-{i + 1}") for i, q in enumerate(EXAM)]
    (ROOT / "data" / "exam.js").write_text(
        "/* Practice Exam A: fresh questions, none repeated from the quiz bank. Generated from content/data_src/exam.py. */\n"
        "window.EXAM_A = [\n" + ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in rows) + "\n];\n",
        encoding="utf-8")
    for t, f, b in CARDS:
        assert t in TOPICS, f"card {f}: unknown topic {t}"
    rows = [{"topic": t, "front": f, "back": b} for t, f, b in CARDS]
    (ROOT / "data" / "flashcards.js").write_text(
        "/* Flashcards: { topic, front, back }. Generated from content/data_src/cards.py. */\n"
        "window.FLASHCARDS = [\n" + ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in rows) + "\n];\n",
        encoding="utf-8")
    print(f"built data: {len(BANK)} quiz questions, {len(EXAM)} exam questions, {len(CARDS)} flashcards")


if __name__ == "__main__":
    main()
