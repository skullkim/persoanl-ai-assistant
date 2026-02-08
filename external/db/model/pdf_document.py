from datetime import datetime
from sqlmodel import SQLModel, Field


class PdfDocument(SQLModel, table=True):
    """PDF 문서 메타데이터"""

    __tablename__ = "pdf_documents"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    author: str | None = None
    file_hash: str | None = None
    total_pages: int | None = None
    category: str | None = None
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
