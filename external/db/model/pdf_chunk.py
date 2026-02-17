from datetime import datetime
from sqlmodel import SQLModel, Field


class PdfChunk(SQLModel, table=True):
    """PDF 문서 청크"""

    __tablename__ = "pdf_chunks"

    id: int | None = Field(default=None, primary_key=True)
    document_id: int
    chunk_index: int
    content: str
    page_start: int | None = None
    page_end: int | None = None
    token_count: int | None = None
    created_at: datetime = Field(default_factory=datetime.now)
