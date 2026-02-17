import logging
from sqlmodel.ext.asyncio.session import AsyncSession

from service.llm_service import get_embedding
from external.db.repository import EmbeddingRepository, NewsRepository, PdfChunkRepository

logger = logging.getLogger(__name__)


async def embed_single(
    source_type: str,
    source_id: int,
    content: str,
    session: AsyncSession,
    metadata: dict | None = None,
) -> bool:
    """단일 항목을 임베딩합니다. 이미 존재하면 스킵합니다.

    Returns:
        True: 새로 임베딩 생성, False: 이미 존재하여 스킵
    """
    existing = await EmbeddingRepository.find_by_source(source_type, source_id, session)
    if existing:
        return False

    vector = await get_embedding(content)
    await EmbeddingRepository.save(
        source_type=source_type,
        source_id=source_id,
        content=content,
        embedding=vector,
        session=session,
        metadata=metadata,
    )
    return True


async def embed_all_news(session: AsyncSession) -> int:
    """임베딩되지 않은 뉴스만 조회하여 임베딩합니다.

    Returns:
        새로 임베딩된 뉴스 수
    """
    articles = await NewsRepository.find_not_embedded(session)
    if not articles:
        logger.info("[임베딩] 임베딩할 신규 뉴스 없음")
        return 0

    logger.info(f"[임베딩] 미임베딩 뉴스 {len(articles)}건 발견")
    embedded_count = 0
    for article in articles:
        content = f"{article.title}\n{(article.content or '')[:1000]}"
        metadata = {
            "category": article.category,
            "source": article.source,
            "upload_date": article.upload_date,
        }

        try:
            created = await embed_single("news", article.id, content, session, metadata)
            if created:
                embedded_count += 1
                if embedded_count % 10 == 0:
                    logger.info(f"[임베딩] 뉴스 {embedded_count}건 처리 중...")
        except Exception as e:
            logger.error(f"[임베딩] 뉴스 id={article.id} 실패: {e}")

    logger.info(f"[임베딩] 뉴스 {embedded_count}건 임베딩 완료")
    return embedded_count


async def embed_pdf_chunks(document_id: int, session: AsyncSession) -> int:
    """PDF 문서의 청크들을 임베딩합니다.

    Returns:
        새로 임베딩된 청크 수
    """
    chunks = await PdfChunkRepository.find_by_document_id(document_id, session)
    if not chunks:
        logger.info(f"[임베딩] document_id={document_id} 청크 없음")
        return 0

    embedded_count = 0
    for chunk in chunks:
        if not chunk.id:
            continue

        metadata = {
            "document_id": document_id,
            "chunk_index": chunk.chunk_index,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
        }

        try:
            created = await embed_single("pdf_chunk", chunk.id, chunk.content, session, metadata)
            if created:
                embedded_count += 1
        except Exception as e:
            logger.error(f"[임베딩] 청크 id={chunk.id} 실패: {e}")

    logger.info(f"[임베딩] document_id={document_id} 청크 {embedded_count}건 완료")
    return embedded_count


async def search_similar_context(
    query: str,
    session: AsyncSession,
    limit: int = 5,
    source_type: str | None = None,
) -> list[dict]:
    """질문과 유사한 컨텍스트를 검색합니다.

    Returns:
        [{"content": str, "source_type": str, "source_id": int, "score": float, "metadata": dict}, ...]
    """
    query_vector = await get_embedding(query)
    results = await EmbeddingRepository.search_similar_with_score(
        query_vector, session, limit=limit, source_type=source_type
    )

    contexts = []
    for embedding, distance in results:
        score = 1.0 - distance  # 코사인 거리 → 유사도 변환
        contexts.append({
            "content": embedding.content,
            "source_type": embedding.source_type,
            "source_id": embedding.source_id,
            "score": round(score, 4),
            "metadata": embedding.extra_data or {},
        })

    return contexts
