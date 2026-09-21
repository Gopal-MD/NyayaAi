"""Section-aware document chunker for legal source documents."""
import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    chunk_id: str
    source_id: str
    section_number: str
    section_title: str
    content: str
    metadata: dict = field(default_factory=dict)


_HEADING_RE = re.compile(
    r"^(?:"
    r"(?:Section|Rule|Chapter|Article|Part)\s+\d+[\w.]*"  # Section 12, Rule 3
    r"|(?:\d+[\w.]*\.?\s+[A-Z][^a-z]{2,})"                # 12. SECURITY DEPOSIT
    r"|(?:[A-Z][A-Z\s]{4,})"                               # ALL CAPS HEADING
    r")",
    re.MULTILINE,
)


def chunk_document(
    text: str,
    source_id: str,
    metadata: dict,
    max_chunk_chars: int = 1200,
) -> list[Chunk]:
    """Split document text into section-aware chunks preserving metadata."""
    chunks: list[Chunk] = []
    lines = text.split("\n")
    current_section_num = ""
    current_section_title = ""
    current_lines: list[str] = []
    chunk_counter = 0

    def _flush():
        nonlocal chunk_counter
        content = "\n".join(current_lines).strip()
        if not content:
            return
        # Split oversized sections
        for sub_content in _split_if_large(content, max_chunk_chars):
            chunk_counter += 1
            cid = f"{source_id}_s{current_section_num or '0'}_c{chunk_counter:04d}"
            chunks.append(Chunk(
                chunk_id=cid,
                source_id=source_id,
                section_number=current_section_num,
                section_title=current_section_title,
                content=sub_content,
                metadata={
                    **metadata,
                    "section_number": current_section_num,
                    "section_title": current_section_title,
                    "chunk_id": cid,
                },
            ))

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue

        heading_match = _HEADING_RE.match(stripped)
        if heading_match and len(stripped) < 120:
            _flush()
            current_lines = [stripped]
            # Extract section number
            num_match = re.search(r"\d+[\w.]*", stripped)
            current_section_num = num_match.group(0) if num_match else ""
            current_section_title = stripped[:80]
        else:
            current_lines.append(line)

    _flush()
    return chunks


def _split_if_large(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    # Split on paragraph boundaries
    paragraphs = re.split(r"\n{2,}", text)
    parts: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            parts.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para).strip()
    if current:
        parts.append(current.strip())
    return parts or [text[:max_chars]]
