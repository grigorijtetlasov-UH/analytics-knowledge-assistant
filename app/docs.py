"""Parse metric documents (data/docs/*.md) and split them into chunks for embedding.

A document is YAML frontmatter, one `# Title` line, then `## Section` blocks:

    ---
    id: aov
    name: Average Order Value
    ...
    ---

    # Average Order Value (AOV)

    ## Definition
    ...

Parsing is strict on purpose: a malformed document fails ingestion with a clear message
instead of being indexed half-broken.
"""

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_DOCS_DIR = Path("data/docs")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
# Sections every metric document must have. `reference` documents (conventions) are free-form.
REQUIRED_METRIC_SECTIONS = ("Definition", "Formula", "Calculation on Olist data")


class DocError(Exception):
    """A document does not follow the expected format."""


class DataAvailability(StrEnum):
    """Whether the metric can be calculated from the Olist dataset."""

    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class DocMeta(BaseModel):
    # extra="forbid": a typo in a frontmatter key (e.g. "alias:") is an error, not ignored.
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str
    aliases: list[str] = []
    category: Literal[
        "sales", "customers", "marketing", "operations", "quality", "finance", "reference"
    ]
    unit: str | None = None
    direction: Literal["higher_is_better", "lower_is_better", "context"] | None = None
    data_availability: DataAvailability
    related: list[str] = []


@dataclass(frozen=True)
class Section:
    title: str
    body: str


@dataclass(frozen=True)
class Document:
    meta: DocMeta
    title: str  # the `# ...` line, e.g. "Average Order Value (AOV)"
    sections: list[Section]
    content_hash: str


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    index: int
    section: str
    content: str


def split_sections(markdown: str) -> tuple[str, list[Section]]:
    """Split the body (after frontmatter) into the `# Title` and `## Section` blocks.
    `## ` lines inside ``` code blocks are ignored."""
    title: str | None = None
    sections: list[Section] = []
    current: str | None = None
    lines: list[str] = []
    in_code = False

    def close_section() -> None:
        if current is not None:
            sections.append(Section(current, "\n".join(lines).strip()))

    for line in markdown.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith("## "):
            close_section()
            current, lines = line[3:].strip(), []
        elif not in_code and line.startswith("# ") and title is None and current is None:
            title = line[2:].strip()
        elif current is not None:
            lines.append(line)
        elif line.strip():
            raise DocError(f"text before the first '## ' section: {line!r}")
    close_section()

    if title is None:
        raise DocError("missing '# Title' line")
    return title, sections


def parse_document(text: str) -> Document:
    match = FRONTMATTER_RE.match(text)
    if match is None:
        raise DocError("missing YAML frontmatter between '---' lines")
    try:
        meta = DocMeta.model_validate(yaml.safe_load(match.group(1)))
    except (yaml.YAMLError, ValidationError) as exc:
        raise DocError(f"invalid frontmatter: {exc}") from exc

    title, sections = split_sections(text[match.end() :])
    if meta.category != "reference":
        present = {section.title for section in sections}
        missing = [name for name in REQUIRED_METRIC_SECTIONS if name not in present]
        if missing:
            raise DocError(f"missing sections: {missing}")
    empty = [section.title for section in sections if not section.body]
    if empty:
        raise DocError(f"empty sections: {empty}")

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return Document(meta, title, sections, content_hash)


def load_documents(directory: Path = DEFAULT_DOCS_DIR) -> list[Document]:
    """Parse every *.md file in `directory`; each id must equal its file name."""
    documents: list[Document] = []
    for path in sorted(directory.glob("*.md")):
        try:
            # read_text() turns CRLF into LF, so the hash is the same on every OS.
            document = parse_document(path.read_text(encoding="utf-8"))
        except DocError as exc:
            raise DocError(f"{path.name}: {exc}") from exc
        if document.meta.id != path.stem:
            raise DocError(f"{path.name}: id {document.meta.id!r} must equal the file name")
        documents.append(document)
    return documents


def chunk_header(meta: DocMeta, section: str) -> str:
    """First line of every chunk. Repeating the metric name and aliases in each chunk keeps
    it self-contained: a "Formula" chunk alone would not say which metric it belongs to, and
    a question using an alias ("ДРР", "LTV") should match every section of that metric."""
    aliases = f"; also: {', '.join(meta.aliases)}" if meta.aliases else ""
    return f"{meta.name} ({meta.id}{aliases}) — {section}"


def chunk_document(document: Document) -> list[Chunk]:
    """One chunk per `##` section. Sections are short (a few hundred tokens), so there is
    no need to split them further; tests/test_docs.py guards the maximum size."""
    return [
        Chunk(
            doc_id=document.meta.id,
            index=index,
            section=section.title,
            content=f"{chunk_header(document.meta, section.title)}\n\n{section.body}",
        )
        for index, section in enumerate(document.sections)
    ]
