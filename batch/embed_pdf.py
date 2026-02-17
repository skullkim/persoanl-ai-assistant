"""
PDF 임베딩 배치

./data/pdf/ 폴더의 PDF 파일을 파싱 → 청크 분할 → 임베딩합니다.
이미 처리된 PDF(file_hash 기준)는 스킵합니다 (멱등성).

사용법:
    python -m batch.embed_pdf

배치 실행:
    APP_ENV=dev python -m batch.embed_pdf
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from external.pdf_parser import extract_text_from_pdf, extract_pages_text
from service.text_chunker import chunk_pages
from service.embedding_service import embed_pdf_chunks
from external.db import init_db, close_db, transactional
from external.db.model import PdfDocument, PdfChunk
from external.db.repository import PdfDocumentRepository, PdfChunkRepository

logger = logging.getLogger(__name__)

PDF_DIR = Path("./data/pdf")


@transactional
async def process_pdf(file_path: str, session=None) -> int:
    """단일 PDF를 파싱 → 청크 → 임베딩합니다.

    Returns:
        임베딩된 청크 수
    """
    _, metadata = extract_text_from_pdf(file_path)

    # 파일 해시로 중복 체크
    existing = await PdfDocumentRepository.find_by_hash(metadata["file_hash"], session)
    if existing:
        print(f"  [스킵] 이미 처리된 PDF: {metadata['title']}")
        return 0

    # PDF 문서 메타데이터 저장
    pdf_doc = PdfDocument(
        title=metadata["title"],
        author=metadata["author"],
        file_hash=metadata["file_hash"],
        total_pages=metadata["total_pages"],
    )
    pdf_doc = await PdfDocumentRepository.save(pdf_doc, session)
    print(f"  [저장] PDF 문서: {pdf_doc.title} (id={pdf_doc.id})")

    # 페이지별 텍스트 추출 → 청크 분할
    pages = extract_pages_text(file_path)
    chunk_dicts = chunk_pages(pages, chunk_size=1000, overlap=200)

    if not chunk_dicts:
        print(f"  [경고] 텍스트 추출 실패: {metadata['title']}")
        return 0

    # 청크 저장
    chunks = []
    for cd in chunk_dicts:
        chunk = PdfChunk(
            document_id=pdf_doc.id,
            chunk_index=cd["chunk_index"],
            content=cd["content"],
            page_start=cd["page_start"],
            page_end=cd["page_end"],
            token_count=len(cd["content"]),
        )
        chunks.append(chunk)

    await PdfChunkRepository.save_all(chunks, session)
    print(f"  [저장] {len(chunks)}개 청크")

    # 청크 임베딩
    # flush 후 청크 ID가 할당되었으므로 다시 조회
    embedded = await embed_pdf_chunks(pdf_doc.id, session)
    print(f"  [임베딩] {embedded}개 청크 임베딩 완료")

    return embedded


async def run_batch():
    """PDF 임베딩 배치를 실행합니다."""
    start_time = datetime.now()
    print(f"=== PDF 임베딩 배치 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")

    if not PDF_DIR.exists():
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[정보] PDF 디렉토리 생성됨: {PDF_DIR}")

    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[정보] PDF 파일 없음 ({PDF_DIR})")
        return

    print(f"[정보] {len(pdf_files)}개 PDF 발견")

    try:
        await init_db()

        total_embedded = 0
        for pdf_path in pdf_files:
            print(f"\n[처리] {pdf_path.name}")
            try:
                count = await process_pdf(str(pdf_path))
                total_embedded += count
            except Exception as e:
                print(f"  [오류] {pdf_path.name} 처리 실패: {e}")

        duration = (datetime.now() - start_time).total_seconds()
        print(f"\n=== PDF 임베딩 배치 완료 ===")
        print(f"  - PDF 파일: {len(pdf_files)}개")
        print(f"  - 신규 임베딩: {total_embedded}건")
        print(f"  - 소요시간: {duration:.2f}초")

    except Exception as e:
        print(f"[오류] PDF 임베딩 배치 실패: {e}")
        raise
    finally:
        await close_db()


def main():
    """배치 진입점"""
    asyncio.run(run_batch())


if __name__ == "__main__":
    main()
