from pydantic import BaseModel


class NewsItemResponse(BaseModel):
    id: str
    title: str
    summary: str
    content: str
    category: str
    date: str
    source: str
