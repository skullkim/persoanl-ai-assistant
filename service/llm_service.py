from external.ollama_client import get_llm, get_embeddings
from config.env_setting import settings


async def generate_text(prompt: str) -> str:
    """LLM을 사용하여 텍스트를 생성합니다."""
    llm = get_llm()
    response = await llm.ainvoke(prompt)
    return response.content


async def get_embedding(text: str) -> list[float]:
    """텍스트의 임베딩 벡터를 반환합니다."""
    embeddings = get_embeddings()
    vector = await embeddings.aembed_query(text)
    return vector


def get_current_model_info() -> dict:
    """현재 설정된 모델 정보를 반환합니다."""
    return {
        "llm_model": settings.LLM_MODEL,
        "embed_model": settings.EMBED_MODEL,
        "ollama_host": settings.OLLAMA_HOST,
    }
