import re
from pathlib import Path

import psycopg
import pytest

from app.docs import (
    DataAvailability,
    DocError,
    chunk_document,
    load_documents,
    parse_document,
)
from app.load_olist import load
from app.migrate import migrate

OLIST_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "olist_sample"
SQL_BLOCK_RE = re.compile(r"```sql\n(.*?)```", re.DOTALL)
LINK_RE = re.compile(r"\]\(([a-z0-9_]+)\.md\)")
# ~600 tokens. Sections are meant to be short; a bigger one should be split into sections.
MAX_CHUNK_CHARS = 2500

VALID_DOC = """\
---
id: demo
name: Demo metric
aliases: [DM]
category: sales
data_availability: full
---

# Demo metric

## Definition
What it is.

## Formula
```
demo = a / b
```

## Calculation on Olist data
```sql
-- ## not a heading inside code
SELECT 1;
```
"""


def doc_files() -> list[Path]:
    return sorted(Path("data/docs").glob("*.md"))


# --- parser unit tests ---


def test_parse_valid_document() -> None:
    document = parse_document(VALID_DOC)
    assert document.meta.id == "demo"
    assert document.meta.unit is None  # optional fields may be omitted
    assert document.meta.data_availability is DataAvailability.FULL
    assert document.title == "Demo metric"
    assert [s.title for s in document.sections] == [
        "Definition",
        "Formula",
        "Calculation on Olist data",
    ]


def test_heading_inside_code_block_is_not_a_section() -> None:
    sections = parse_document(VALID_DOC).sections
    assert "-- ## not a heading inside code" in sections[-1].body


def test_missing_frontmatter_is_an_error() -> None:
    with pytest.raises(DocError, match="frontmatter"):
        parse_document("# Demo\n\n## Definition\nx\n")


def test_unknown_frontmatter_key_is_an_error() -> None:
    with pytest.raises(DocError, match="invalid frontmatter"):
        parse_document(VALID_DOC.replace("aliases:", "alias:"))


def test_invalid_data_availability_is_an_error() -> None:
    with pytest.raises(DocError, match="invalid frontmatter"):
        parse_document(VALID_DOC.replace("data_availability: full", "data_availability: yes"))


def test_metric_without_required_section_is_an_error() -> None:
    with pytest.raises(DocError, match="missing sections"):
        parse_document(VALID_DOC.replace("## Formula", "## Formulas"))


def test_reference_document_has_free_form_sections() -> None:
    text = VALID_DOC.replace("category: sales", "category: reference").replace(
        "## Formula", "## Anything"
    )
    assert parse_document(text).meta.category == "reference"


def test_text_before_first_section_is_an_error() -> None:
    with pytest.raises(DocError, match="before the first"):
        parse_document(VALID_DOC.replace("# Demo metric\n", "# Demo metric\nstray text\n"))


def test_chunks_carry_metric_name_aliases_and_section() -> None:
    chunks = chunk_document(parse_document(VALID_DOC))
    assert [c.index for c in chunks] == [0, 1, 2]
    assert chunks[1].section == "Formula"
    assert chunks[1].content.startswith("Demo metric (demo; also: DM) — Formula\n\n")
    assert "demo = a / b" in chunks[1].content


def test_id_must_match_file_name(tmp_path: Path) -> None:
    (tmp_path / "other.md").write_text(VALID_DOC, encoding="utf-8")
    with pytest.raises(DocError, match="must equal the file name"):
        load_documents(tmp_path)


# --- checks on the real documents in data/docs ---


def test_all_documents_parse() -> None:
    documents = load_documents()
    assert [d.meta.id for d in documents] == [p.stem for p in doc_files()]


def test_related_and_links_point_to_existing_documents() -> None:
    ids = {p.stem for p in doc_files()}
    broken = []
    for document in load_documents():
        broken += [(document.meta.id, r) for r in document.meta.related if r not in ids]
    for path in doc_files():
        text = path.read_text(encoding="utf-8")
        broken += [(path.stem, link) for link in LINK_RE.findall(text) if link not in ids]
    assert broken == []


def test_chunks_are_small_enough() -> None:
    too_big = [
        (chunk.doc_id, chunk.section, len(chunk.content))
        for document in load_documents()
        for chunk in chunk_document(document)
        if len(chunk.content) > MAX_CHUNK_CHARS
    ]
    assert too_big == []


@pytest.mark.db
def test_sql_examples_run(db_conn: psycopg.Connection) -> None:
    """Every ```sql block in the docs runs against the real schema. The synthetic Olist
    fixture is loaded so that ratios do not divide by zero on empty tables."""
    migrate(db_conn)
    load(db_conn, OLIST_FIXTURE_DIR)
    failures = []
    for path in doc_files():
        for sql in SQL_BLOCK_RE.findall(path.read_text(encoding="utf-8")):
            try:
                db_conn.execute(sql).fetchall()
            except psycopg.Error as exc:
                failures.append(f"{path.name}: {exc}")
    assert failures == []
