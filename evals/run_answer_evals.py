"""Answer evals: run /ask's pipeline on evals/answer_cases.json with real APIs.

Usage: uv run python -m evals.run_answer_evals --label models [--models claude-opus-5-5 ...]
       [--repeats 1] [--ids a01 a05]

Each case goes through app.answer.answer_question (real embeddings, real Claude). Checks
are formal: status, cited documents, clarifying question, required substrings, answer
language (see the description in answer_cases.json). A pipeline error (refusal,
invalid sources) is a failed case, not a crash. Cost and latency are recorded per call.

The full report goes to evals/results/answers_<label>.md; the console gets the summary.
Costs money: measured ~$0.012 per case on Opus 5.5, ~$0.0055 on Sonnet 5.5 (README).
"""

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import anthropic
import psycopg
from openai import OpenAI

from app.answer import Answer, AnswerValidationError, answer_question
from app.config import get_settings
from app.db import connect
from app.embeddings import Embedder, OpenAIEmbedder
from app.llm import LLM, PRICES, AnswerStatus, AnthropicLLM, LLMError
from evals.run_evals import RESULTS_DIR, CachedEmbedder

CASES_PATH = Path("evals/answer_cases.json")
CYRILLIC_RE = re.compile(r"[а-яіїєґёыэъ]", re.IGNORECASE)
RUSSIAN_ONLY_RE = re.compile(r"[ёыэъ]", re.IGNORECASE)
LETTER_RE = re.compile(r"[^\W\d_]")


@dataclass(frozen=True)
class AnswerCase:
    id: str
    kind: str
    lang: str
    question: str
    expected_status: AnswerStatus
    must_cite: frozenset[str]
    answer_contains: tuple[str, ...] = ()


@dataclass
class Outcome:
    case: AnswerCase
    model: str
    run: int
    answer: Answer | None
    error: str | None
    seconds: float
    failures: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


def load_answer_cases(path: Path = CASES_PATH) -> list[AnswerCase]:
    items = json.loads(path.read_text(encoding="utf-8"))["items"]
    return [
        AnswerCase(
            id=item["id"],
            kind=item["kind"],
            lang=item["lang"],
            question=item["question"],
            expected_status=AnswerStatus(item["expected_status"]),
            must_cite=frozenset(item["must_cite"]),
            answer_contains=tuple(item.get("answer_contains", [])),
        )
        for item in items
    ]


def check(case: AnswerCase, answer: Answer) -> list[str]:
    """Reasons the answer fails the case; empty when it passes."""
    failures = []
    if answer.status != case.expected_status:
        failures.append(f"status {answer.status}, expected {case.expected_status}")
    missing = sorted(case.must_cite - {s.doc_id for s in answer.sources})
    if missing:
        failures.append(f"not cited: {', '.join(missing)}")
    if case.expected_status == AnswerStatus.AMBIGUOUS and not answer.clarifying_question:
        failures.append("no clarifying question")
    for text in case.answer_contains:
        if text.lower() not in answer.answer.lower():
            failures.append(f"answer lacks {text!r}")
    failures += language_failures(case.lang, answer.answer)
    return failures


def language_failures(lang: str, text: str) -> list[str]:
    """Rough language check, enough to catch an answer in the wrong language.

    Ukrainian answers keep SQL and metric names in English (~40% Cyrillic letters in
    practice), so "uk" only needs some Cyrillic, and none of the letters Ukrainian lacks
    (ы, э, ъ, ё): Russian aliases in the docs once pulled an answer into Russian. English
    answers may quote a term like «ДРР», so up to 20% Cyrillic is allowed."""
    letters = LETTER_RE.findall(text)
    cyrillic_share = len(CYRILLIC_RE.findall(text)) / max(len(letters), 1)
    if RUSSIAN_ONLY_RE.search(text):
        return ["answer is in Russian"]
    if lang == "uk" and cyrillic_share == 0:
        return ["answer is not in Ukrainian"]
    if lang == "en" and cyrillic_share > 0.2:
        return ["answer is not in English"]
    return []


def run_case(
    conn: psycopg.Connection,
    case: AnswerCase,
    embedder: Embedder,
    llm: LLM,
    min_similarity: float,
    run: int,
) -> Outcome:
    start = time.perf_counter()
    try:
        answer = answer_question(conn, case.question, embedder, llm, min_similarity=min_similarity)
        error = None
    except (LLMError, AnswerValidationError) as exc:
        answer, error = None, f"{type(exc).__name__}: {exc}"
    seconds = time.perf_counter() - start
    outcome = Outcome(case, llm.model, run, answer, error, seconds)
    outcome.failures = [error] if answer is None else check(case, answer)
    return outcome


def summary_table(outcomes: list[Outcome], models: list[str]) -> str:
    lines = [
        "| model | passed | failed cases | cost per question | total cost | mean latency, s |"
        " cache read tokens |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for model in models:
        rows = [o for o in outcomes if o.model == model]
        # Only calls that reached the LLM: the similarity gate costs nothing and takes ~0 s.
        llm_rows = [o for o in rows if o.answer is not None and o.answer.usage is not None]
        costs = [o.answer.cost_usd or 0.0 for o in llm_rows if o.answer]
        cache = sum(
            o.answer.usage.cache_read_input_tokens for o in llm_rows if o.answer and o.answer.usage
        )
        n = max(len(llm_rows), 1)
        failed = sorted({o.case.id for o in rows if not o.passed})
        lines.append(
            f"| {model} | {sum(o.passed for o in rows)}/{len(rows)} | {', '.join(failed) or '-'}"
            f" | ${sum(costs) / n:.4f} | ${sum(costs):.4f}"
            f" | {sum(o.seconds for o in llm_rows) / n:.1f} | {cache} |"
        )
    return "\n".join(lines)


def details_section(outcomes: list[Outcome]) -> str:
    lines = [
        "| model | run | id | kind | status | sources | cost | s | result |",
        "|---|---:|---|---|---|---|---:|---:|---|",
    ]
    for o in outcomes:
        a = o.answer
        status = "error" if a is None else a.status
        sources = "" if a is None else ", ".join(dict.fromkeys(s.doc_id for s in a.sources))
        cost = "" if a is None or a.cost_usd is None else f"${a.cost_usd:.4f}"
        result = "pass" if o.passed else "FAIL: " + "; ".join(o.failures)
        lines.append(
            f"| {o.model} | {o.run} | {o.case.id} | {o.case.kind} | {status} | {sources}"
            f" | {cost} | {o.seconds:.1f} | {result} |"
        )
    return "\n".join(lines)


def answers_section(outcomes: list[Outcome]) -> str:
    """Full answers of the first run, for reading what the models actually said."""
    parts = []
    for o in outcomes:
        if o.run != 1:
            continue
        text = o.error if o.answer is None else o.answer.answer
        question = "" if o.answer is None else o.answer.clarifying_question or ""
        clarify = f"\n\n*Clarifying question:* {question}" if question else ""
        parts.append(f"### {o.model} · {o.case.id} · {o.case.question}\n\n{text}{clarify}\n")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True, help="report name, e.g. models")
    parser.add_argument("--models", nargs="+", choices=list(PRICES), default=list(PRICES))
    parser.add_argument("--repeats", type=int, default=1, help="runs per case and model")
    parser.add_argument("--ids", nargs="+", help="run only these case ids (smoke tests)")
    parser.add_argument("--note", default="", help="caveats written at the top of the report")
    args = parser.parse_args()

    settings = get_settings()
    if settings.openai_api_key is None or settings.anthropic_api_key is None:
        print("OPENAI_API_KEY and ANTHROPIC_API_KEY must be set in .env", file=sys.stderr)
        return 1
    embedder = CachedEmbedder(
        OpenAIEmbedder(
            OpenAI(api_key=settings.openai_api_key.get_secret_value()),
            settings.embedding_model,
            settings.embedding_dimensions,
        ),
        settings.embedding_dimensions,
    )
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value())
    cases = [c for c in load_answer_cases() if not args.ids or c.id in args.ids]

    outcomes: list[Outcome] = []
    with connect(autocommit=True) as conn:
        for model in args.models:
            llm = AnthropicLLM(client, model, settings.llm_effort)
            for run in range(1, args.repeats + 1):
                for case in cases:
                    outcome = run_case(
                        conn, case, embedder, llm, settings.off_topic_min_similarity, run
                    )
                    outcomes.append(outcome)
                    mark = "pass" if outcome.passed else "FAIL"
                    print(f"{model} run {run} {case.id}: {mark}", flush=True)

    table = summary_table(outcomes, args.models)
    note = f"> **Note.** {args.note}\n\n" if args.note else ""
    report = (
        f"# Answer eval: {args.label}\n\n{note}"
        f"{len(cases)} cases x {args.repeats} run(s) per model, effort `{settings.llm_effort}`, "
        f"off-topic threshold {settings.off_topic_min_similarity}. "
        "Cost and latency are averaged over questions that reached the LLM.\n\n"
        f"## Summary\n\n{table}\n\n## Cases\n\n{details_section(outcomes)}\n\n"
        f"## Answers (run 1)\n\n{answers_section(outcomes)}"
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"answers_{args.label}.md"
    out.write_text(report, encoding="utf-8")
    print(f"\n{table}\n\nfull report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
