from langchain_ollama import ChatOllama, OllamaEmbeddings

from config.env_setting import settings


def get_llm() -> ChatOllama:
    """요약용 ChatOllama 인스턴스를 반환합니다."""
    return ChatOllama(
        base_url=settings.OLLAMA_HOST,
        model=settings.LLM_MODEL,
        temperature=0.3,
    )


def get_embeddings() -> OllamaEmbeddings:
    """OllamaEmbeddings 인스턴스를 반환합니다."""
    return OllamaEmbeddings(
        base_url=settings.OLLAMA_HOST,
        model=settings.EMBED_MODEL,
    )
