from datetime import datetime
from sqlmodel import SQLModel, Field, Column, UniqueConstraint
from pgvector.sqlalchemy import Vector
from sqlalchemy import Index


class Embedding(SQLModel, table=True):
    """통합 임베딩 테이블 (벡터 검색용)"""

    __tablename__ = "embeddings"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id"),
        Index(
            "embeddings_vector_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    source_type: str  # 'news', 'video', 'pdf'
    source_id: int
    content: str
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(1024)))
    metadata: dict | None = Field(default=None, sa_type_kwargs={"as_json": True})
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
