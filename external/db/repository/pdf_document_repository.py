from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import PdfDocument


class PdfDocumentRepository:
    """PDF 문서 CRUD 레포지토리"""

    @staticmethod
    async def save(pdf_document: PdfDocument, session: AsyncSession) -> PdfDocument:
        """PDF 문서를 저장합니다."""
        session.add(pdf_document)
        await session.flush()
        await session.refresh(pdf_document)
        return pdf_document

    @staticmethod
    async def find_by_id(document_id: int, session: AsyncSession) -> PdfDocument | None:
        """ID로 PDF 문서를 조회합니다."""
        return await session.get(PdfDocument, document_id)

    @staticmethod
    async def find_by_hash(file_hash: str, session: AsyncSession) -> PdfDocument | None:
        """파일 해시로 PDF 문서를 조회합니다 (중복 체크용)."""
        stmt = select(PdfDocument).where(PdfDocument.file_hash == file_hash)
        result = await session.exec(stmt)
        return result.first()

    @staticmethod
    async def find_all(session: AsyncSession, limit: int = 100) -> list[PdfDocument]:
        """PDF 문서 목록을 조회합니다."""
        stmt = select(PdfDocument).order_by(PdfDocument.created_at.desc()).limit(limit)
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_by_category(category: str, session: AsyncSession, limit: int = 100) -> list[PdfDocument]:
        """카테고리별 PDF 문서를 조회합니다."""
        stmt = (
            select(PdfDocument)
            .where(PdfDocument.category == category)
            .order_by(PdfDocument.created_at.desc())
            .limit(limit)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_by_author(author: str, session: AsyncSession, limit: int = 100) -> list[PdfDocument]:
        """저자별 PDF 문서를 조회합니다."""
        stmt = (
            select(PdfDocument)
            .where(PdfDocument.author == author)
            .order_by(PdfDocument.created_at.desc())
            .limit(limit)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def update(document_id: int, session: AsyncSession, **kwargs) -> PdfDocument | None:
        """PDF 문서를 수정합니다."""
        pdf_document = await session.get(PdfDocument, document_id)
        if pdf_document:
            for key, value in kwargs.items():
                if hasattr(pdf_document, key):
                    setattr(pdf_document, key, value)
            await session.flush()
            await session.refresh(pdf_document)
            return pdf_document
        return None

    @staticmethod
    async def delete(document_id: int, session: AsyncSession) -> bool:
        """PDF 문서를 삭제합니다."""
        pdf_document = await session.get(PdfDocument, document_id)
        if pdf_document:
            await session.delete(pdf_document)
            return True
        return False
