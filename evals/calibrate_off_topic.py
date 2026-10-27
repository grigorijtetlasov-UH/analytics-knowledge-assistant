"""Measure top-1 similarity for on-topic and off-topic questions to pick OFF_TOPIC_MIN_SIMILARITY.

Usage: uv run python -m evals.calibrate_off_topic

On-topic: every question of evals/testset.json. Off-topic: evals/off_topic.json. For each
question the score of the best chunk (cosine similarity, vector search) is recorded.
Below the threshold /ask answers off_topic without calling the LLM, so a threshold above
any on-topic score would reject real questions. The suggestion is therefore placed a
margin below the lowest on-topic score; off-topic questions above it still reach the
model, which is instructed to answer off_topic itself.

The report goes to evals/results/off_topic_threshold.md.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from app.config import get_settings
from app.db import connect
from app.embeddings import OpenAIEmbedder
from app.retrieval import search_vector
from evals.run_evals import RESULTS_DIR, CachedEmbedder, load_cases

OFF_TOPIC_PATH = Path("evals/off_topic.json")
# Safety margin below the lowest on-topic score: questions written by other people
# (milestone 6) will likely score lower than ours. The two errors are not symmetric: a
# threshold too high silently rejects a real question, while one too low only costs an LLM
# call (the model can still answer off_topic). So the margin errs on the low side.
MARGIN = 0.05


@dataclass(frozen=True)
class Scored:
    id: str
    group: str  # "on-topic" | "off-topic far" | "off-topic near"
    lang: str
    question: str
    score: float
    top_doc: str


def load_off_topic(path: Path = OFF_TOPIC_PATH) -> list[dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))["items"]


def suggest_threshold(on_topic_scores: list[float], margin: float = MARGIN) -> float:
    """Lowest on-topic score minus the margin, rounded down to 2 decimals."""
    return int((min(on_topic_scores) - margin) * 100) / 100


def report(rows: list[Scored], threshold: float) -> str:
    def stats(group: str) -> str:
        scores = sorted(r.score for r in rows if r.group == group)
        return f"| {group} | {len(scores)} | {scores[0]:.3f} | {scores[-1]:.3f} |"

    groups = ["on-topic", "off-topic far", "off-topic near"]
    below = {g: sum(1 for r in rows if r.group == g and r.score < threshold) for g in groups}
    lines = [
        "# Off-topic threshold calibration",
        "",
        f"Suggested `OFF_TOPIC_MIN_SIMILARITY` = **{threshold:.2f}** "
        f"(lowest on-topic score minus {MARGIN}).",
        "",
        "> **Note.** The on-topic questions were written by the same person as the docs and",
        "> their aliases. Re-check this threshold on independently written questions in",
        "> milestone 6 before trusting it.",
        "",
        "| group | n | min | max |",
        "|---|---:|---:|---:|",
        *(stats(g) for g in groups),
        "",
        "Rejected by the threshold (no LLM call): "
        + ", ".join(f"{g} {below[g]}/{sum(1 for r in rows if r.group == g)}" for g in groups)
        + ".",
        "",
        "## All questions, lowest score first",
        "",
        "| score | group | id | lang | top doc | question |",
        "|---:|---|---|---|---|---|",
        *(
            f"| {r.score:.3f} | {r.group} | {r.id} | {r.lang} | {r.top_doc} | {r.question} |"
            for r in sorted(rows, key=lambda r: r.score)
        ),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    settings = get_settings()
    if settings.openai_api_key is None:
        print("OPENAI_API_KEY is not set in .env", file=sys.stderr)
        return 1
    client = OpenAI(api_key=settings.openai_api_key.get_secret_value())
    embedder = CachedEmbedder(
        OpenAIEmbedder(client, settings.embedding_model, settings.embedding_dimensions),
        settings.embedding_dimensions,
    )
    questions = [(c.id, "on-topic", c.lang, c.question) for c in load_cases()] + [
        (o["id"], f"off-topic {o['kind']}", o["lang"], o["question"]) for o in load_off_topic()
    ]
    embeddings = embedder.embed([q[3] for q in questions])
    rows = []
    with connect() as conn:
        for (qid, group, lang, question), embedding in zip(questions, embeddings, strict=True):
            top = search_vector(conn, embedding, embedder.model, k=1)[0]
            rows.append(Scored(qid, group, lang, question, top.score, top.doc_id))

    threshold = suggest_threshold([r.score for r in rows if r.group == "on-topic"])
    text = report(rows, threshold)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "off_topic_threshold.md"
    out.write_text(text, encoding="utf-8")
    # Summary lines are ASCII; questions with Cyrillic go to the file only (Windows console).
    print("\n".join(line for line in text.splitlines() if line.isascii())[:2000])
    print(f"\nfull report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
