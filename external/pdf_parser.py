import hashlib
import logging
from pathlib import Path

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> tuple[str, dict]:
    """PDF에서 텍스트와 메타데이터를 추출합니다.

    Returns:
        (전체 텍스트, 메타데이터) 튜플
        메타데이터: {title, author, total_pages, file_hash}
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {file_path}")

    reader = PdfReader(file_path)
    info = reader.metadata

    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    full_text = "\n".join(pages_text)

    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    metadata = {
        "title": (info.title if info and info.title else path.stem),
        "author": (info.author if info and info.author else None),
        "total_pages": len(reader.pages),
        "file_hash": file_hash,
    }

    logger.info(f"[PDF] '{metadata['title']}' 추출 완료 ({metadata['total_pages']}페이지, {len(full_text)}자)")
    return full_text, metadata


def extract_pages_text(file_path: str) -> list[tuple[int, str]]:
    """PDF에서 페이지별 텍스트를 추출합니다.

    Returns:
        [(page_number, text), ...] 리스트 (1-indexed)
    """
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text and text.strip():
            pages.append((i, text))
    return pages
