from pathlib import Path

from app.answer import Answer, Source
from app.llm import AnswerStatus
from evals.run_answer_evals import AnswerCase, check, language_failures, load_answer_cases

DOC_IDS = {p.stem for p in Path("data/docs").glob("*.md")}


def case(**overrides: object) -> AnswerCase:
    values: dict[str, object] = {
        "id": "a01",
        "kind": "answered",
        "lang": "en",
        "question": "What is AOV?",
        "expected_status": AnswerStatus.ANSWERED,
        "must_cite": frozenset({"aov"}),
    }
    values.update(overrides)
    return AnswerCase(**values)  # type: ignore[arg-type]


def answer(
    status: AnswerStatus = AnswerStatus.ANSWERED,
    text: str = "AOV = GMV / orders [S1]",
    doc_ids: tuple[str, ...] = ("aov",),
    clarifying_question: str | None = None,
) -> Answer:
    sources = [Source(d, d, "Formula") for d in doc_ids]
    return Answer(status, text, clarifying_question, sources)


def test_cases_file_is_valid() -> None:
    cases = load_answer_cases()
    assert len({c.id for c in cases}) == len(cases)
    assert all(c.must_cite <= DOC_IDS for c in cases)
    assert {c.lang for c in cases} == {"en", "uk"}
    # Every status is covered, and the DRR ambiguity case exists (CLAUDE.md, milestone 4).
    assert {c.expected_status for c in cases} == set(AnswerStatus)
    assert any(
        c.expected_status == AnswerStatus.AMBIGUOUS and {"acos", "ad_spend_share"} <= c.must_cite
        for c in cases
    )


def test_passing_answer_has_no_failures() -> None:
    assert check(case(), answer()) == []


def test_wrong_status_and_missing_source_fail() -> None:
    failures = check(case(), answer(AnswerStatus.NO_DATA, doc_ids=("gmv",)))
    assert failures == ["status no_data, expected answered", "not cited: aov"]


def test_ambiguous_needs_both_sources_and_a_question() -> None:
    ambiguous = case(
        expected_status=AnswerStatus.AMBIGUOUS, must_cite=frozenset({"acos", "ad_spend_share"})
    )
    failures = check(ambiguous, answer(AnswerStatus.AMBIGUOUS, doc_ids=("acos",)))
    assert failures == ["not cited: ad_spend_share", "no clarifying question"]


def test_required_text_and_language() -> None:
    uk = case(lang="uk", answer_contains=("SELECT",))
    assert check(uk, answer(text="AOV = GMV / orders")) == [
        "answer lacks 'SELECT'",
        "answer is not in Ukrainian",
    ]
    assert check(uk, answer(text="Середній чек: select sum(price) ...")) == []


def test_language_check() -> None:
    assert language_failures("uk", "Середній чек: SELECT sum(price) FROM olist.order_items") == []
    assert language_failures("en", 'In everyday speech "ДРР" means two metrics.') == []
    assert language_failures("en", "Доля рекламных расходов в выручке") == ["answer is in Russian"]
    assert language_failures("uk", "Доля рекламных расходов") == ["answer is in Russian"]
    assert language_failures("en", "Частка реклами у виручці") == ["answer is not in English"]
