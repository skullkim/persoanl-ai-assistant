from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import PdfChunk


class PdfChunkRepository:
    """PDF 청크 CRUD 레포지토리"""

    @staticmethod
    async def save(chunk: PdfChunk, session: AsyncSession) -> PdfChunk:
        """청크를 저장합니다."""
        session.add(chunk)
        await session.flush()
        await session.refresh(chunk)
        return chunk

    @staticmethod
    async def save_all(chunks: list[PdfChunk], session: AsyncSession) -> int:
        """청크 목록을 저장합니다."""
        for chunk in chunks:
            session.add(chunk)
        await session.flush()
        return len(chunks)

    @staticmethod
    async def find_by_document_id(document_id: int, session: AsyncSession) -> list[PdfChunk]:
        """문서 ID로 청크를 조회합니다."""
        stmt = (
            select(PdfChunk)
            .where(PdfChunk.document_id == document_id)
            .order_by(PdfChunk.chunk_index)
        )
        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def find_by_id(chunk_id: int, session: AsyncSession) -> PdfChunk | None:
        """ID로 청크를 조회합니다."""
        return await session.get(PdfChunk, chunk_id)

    @staticmethod
    async def delete_by_document_id(document_id: int, session: AsyncSession) -> int:
        """문서 ID로 청크를 삭제합니다."""
        stmt = select(PdfChunk).where(PdfChunk.document_id == document_id)
        result = await session.exec(stmt)
        chunks = result.all()
        for chunk in chunks:
            await session.delete(chunk)
        return len(chunks)
