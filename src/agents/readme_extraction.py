import re

from mrkdwn_analysis import MarkdownAnalyzer
from pydantic import BaseModel, Field

_IMAGE_RE = re.compile(r"!\[[^\]]*\](\([^)]*\)|\[[^\]]*\])")
_LINK_RE = re.compile(r"\[([^\]]*)\](\([^)]*\)|\[[^\]]*\])")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://\S+")
_SPACES_RE = re.compile(r"[ \t]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")

# Sections that rarely say anything about what the project does or how it compares.
SKIPPED_SECTION_PREFIXES = (
    "license",
    "contributing",
    "contributors",
    "acknowledg",
    "sponsor",
    "backers",
    "star history",
    "citation",
    "table of contents",
    "contents",
    "changelog",
    "code of conduct",
)

MAX_README_CHARS = 6000
MAX_SECTION_CHARS = 1200
MAX_CODE_LINES = 15
MAX_TABLE_ROWS = 10


class ReadmeSection(BaseModel):
    title: str = Field(..., description="The header text of the section.")
    level: int = Field(..., description="The header level (0 for the intro before any header).")
    content: str = Field(..., description="The cleaned text content of the section.")


class ReadmeExtract(BaseModel):
    title: str | None = Field(None, description="The first level-1 header of the README.")
    sections: list[ReadmeSection] = Field(..., description="The README sections in order.")
    truncated: bool = Field(..., description="Whether content was dropped to fit the budget.")

    def to_prompt_text(self) -> str:
        """Render the extract as compact markdown for an LLM prompt."""
        parts = [f"# {self.title}"] if self.title else []
        for section in self.sections:
            if section.level > 0:
                parts.append(f"{'#' * min(section.level + 1, 6)} {section.title}")
            parts.append(section.content)
        if self.truncated:
            parts.append("[README truncated]")
        return "\n\n".join(parts)


def _clean_inline(text: str) -> str:
    """Drop images, HTML and bare URLs; keep link text."""
    text = _IMAGE_RE.sub("", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _URL_RE.sub("", text)
    lines = (_SPACES_RE.sub(" ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def _render_code(content: str, language: str | None) -> str:
    lines = content.splitlines()
    if len(lines) > MAX_CODE_LINES:
        lines = [*lines[:MAX_CODE_LINES], "..."]
    body = "\n".join(lines)
    return f"```{language or ''}\n{body}\n```"


def _render_table(header: list[str], rows: list[list[str]]) -> str:
    rendered = [
        " | ".join(_clean_inline(cell) for cell in row) for row in [header, *rows[:MAX_TABLE_ROWS]]
    ]
    if len(rows) > MAX_TABLE_ROWS:
        rendered.append("...")
    return "\n".join(rendered)


def _render_token(token) -> str:
    match token.type:
        case "paragraph" | "blockquote" | "html_block":
            return _clean_inline(token.content)
        case "ordered_list" | "unordered_list":
            items = (_clean_inline(item["text"]) for item in token.meta["items"])
            return "\n".join(f"- {item}" for item in items if item)
        case "code":
            return _render_code(token.content, token.meta.get("language"))
        case "table":
            return _render_table(token.meta["header"], token.meta["rows"])
        case _:  # hr, frontmatter
            return ""


def _is_skipped(title: str) -> bool:
    normalized = re.sub(r"[^a-z ]", "", title.lower()).strip()
    return normalized.startswith(SKIPPED_SECTION_PREFIXES)


def _parse_tokens(markdown: str) -> list:
    try:
        return MarkdownAnalyzer.from_string(markdown).tokens
    except ValueError:
        # The parser raises on an unclosed code fence; close it and retry.
        return MarkdownAnalyzer.from_string(markdown + "\n```").tokens


def _group_sections(markdown: str) -> tuple[str | None, list[ReadmeSection]]:
    """Group rendered tokens under their headers, dropping boilerplate sections."""
    title: str | None = None
    sections: list[ReadmeSection] = []
    current = ReadmeSection(title="Introduction", level=0, content="")
    skip_level: int | None = None

    for token in _parse_tokens(markdown):
        if token.type == "header":
            header = _clean_inline(token.content)
            if skip_level is not None and token.level > skip_level:
                continue  # subsection of a skipped section
            skip_level = None
            if token.level == 1 and title is None:
                title = header
                continue
            if _is_skipped(header):
                skip_level = token.level
                continue
            sections.append(current)
            current = ReadmeSection(title=header, level=token.level, content="")
            continue

        if skip_level is not None:
            continue
        rendered = _render_token(token)
        if rendered:
            current.content = f"{current.content}\n\n{rendered}" if current.content else rendered
    sections.append(current)
    return title, sections


def extract_readme(markdown: str, max_chars: int = MAX_README_CHARS) -> ReadmeExtract:
    """
    Simplify a README into context for an LLM.

    Removes images, HTML, URLs and boilerplate sections (license, contributors, ...),
    groups the remaining content under its headers, and trims each section and
    the whole README to a character budget.
    """
    title, sections = _group_sections(markdown)

    kept: list[ReadmeSection] = []
    used = 0
    truncated = False
    for section in sections:
        content = _BLANK_LINES_RE.sub("\n\n", section.content).strip()
        if not content:
            continue
        if len(content) > MAX_SECTION_CHARS:
            content = content[:MAX_SECTION_CHARS].rstrip() + " ..."
            truncated = True
        if used + len(content) > max_chars:
            truncated = True
            break
        kept.append(section.model_copy(update={"content": content}))
        used += len(content)

    return ReadmeExtract(title=title, sections=kept, truncated=truncated)
