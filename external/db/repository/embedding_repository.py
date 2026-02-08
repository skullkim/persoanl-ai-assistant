from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from external.db.model import Embedding


class EmbeddingRepository:
    """임베딩 CRUD 레포지토리"""

    @staticmethod
    async def save(
        source_type: str,
        source_id: int,
        content: str,
        embedding: list[float],
        session: AsyncSession,
        metadata: dict | None = None,
    ) -> Embedding:
        """임베딩을 저장합니다."""
        emb = Embedding(
            source_type=source_type,
            source_id=source_id,
            content=content,
            embedding=embedding,
            metadata=metadata,
        )
        session.add(emb)
        await session.flush()
        await session.refresh(emb)
        return emb

    @staticmethod
    async def find_by_id(embedding_id: int, session: AsyncSession) -> Embedding | None:
        """ID로 임베딩을 조회합니다."""
        return await session.get(Embedding, embedding_id)

    @staticmethod
    async def find_by_source(source_type: str, source_id: int, session: AsyncSession) -> Embedding | None:
        """소스 정보로 임베딩을 조회합니다."""
        stmt = select(Embedding).where(
            Embedding.source_type == source_type,
            Embedding.source_id == source_id,
        )
        result = await session.exec(stmt)
        return result.first()

    @staticmethod
    async def search_similar(
        query_embedding: list[float],
        session: AsyncSession,
        limit: int = 5,
        source_type: str | None = None,
    ) -> list[Embedding]:
        """유사한 임베딩을 검색합니다."""
        stmt = select(Embedding).order_by(
            Embedding.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        if source_type:
            stmt = stmt.where(Embedding.source_type == source_type)

        result = await session.exec(stmt)
        return result.all()

    @staticmethod
    async def delete(embedding_id: int, session: AsyncSession) -> bool:
        """임베딩을 삭제합니다."""
        embedding = await session.get(Embedding, embedding_id)
        if embedding:
            await session.delete(embedding)
            return True
        return False

    @staticmethod
    async def delete_by_source(source_type: str, source_id: int, session: AsyncSession) -> bool:
        """소스 정보로 임베딩을 삭제합니다."""
        stmt = select(Embedding).where(
            Embedding.source_type == source_type,
            Embedding.source_id == source_id,
        )
        result = await session.exec(stmt)
        embedding = result.first()
        if embedding:
            await session.delete(embedding)
            return True
        return False
