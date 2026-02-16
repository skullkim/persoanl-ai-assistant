from pydantic import BaseModel


class NewsItemResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str
    date: str
    source: str
