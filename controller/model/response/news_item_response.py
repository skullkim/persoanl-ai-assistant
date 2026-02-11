from pydantic import BaseModel


class NewsItemResponse(BaseModel):
    id: str
    title: str
    summary: str | None = None
    content: str
    category: str
    date: str
    source: str
