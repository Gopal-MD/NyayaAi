"""Document text extraction with PDF, DOCX, and image support."""
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path


@dataclass(frozen=True)
class PageText:
    page: int
    text: str
    method: str


def _extract_pdf(content: bytes) -> list[PageText]:
    import fitz

    document = fitz.open(stream=content, filetype="pdf")
    pages = [PageText(index + 1, page.get_text("text").strip(), "pymupdf") for index, page in enumerate(document)]
    if pages and sum(len(page.text) for page in pages) / len(pages) >= 50:
        return pages

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return pages

    ocr_pages: list[PageText] = []
    for index, page in enumerate(document):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.open(BytesIO(pixmap.tobytes("png")))
        ocr_pages.append(PageText(index + 1, pytesseract.image_to_string(image, lang="eng+tam").strip(), "ocr"))
    return ocr_pages


def _extract_docx(content: bytes) -> list[PageText]:
    from docx import Document

    document = Document(BytesIO(content))
    text = "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip())
    return [PageText(1, text, "python-docx")]


def _extract_image(content: bytes) -> list[PageText]:
    from PIL import Image
    import pytesseract

    image = Image.open(BytesIO(content))
    return [PageText(1, pytesseract.image_to_string(image, lang="eng+tam").strip(), "ocr")]


def extract_document(content: bytes, filename: str, extension: str | None = None) -> list[PageText]:
    suffix = (extension or Path(filename).suffix).lower()
    if suffix == ".pdf":
        return _extract_pdf(content)
    if suffix == ".docx":
        return _extract_docx(content)
    if suffix in {".jpg", ".jpeg", ".png"}:
        return _extract_image(content)
    raise ValueError(f"Unsupported document format: {suffix or 'unknown'}")


def extract_pdf(path: str) -> list[PageText]:
    return extract_document(Path(path).read_bytes(), path, ".pdf")


def extract_docx(path: str) -> list[PageText]:
    return extract_document(Path(path).read_bytes(), path, ".docx")
