from pydantic import BaseModel


class NewsArticleResponse(BaseModel):
    title: str
    summary: str
    url: str
    image_url: str | None = None
    published_at: str | None = None
    source: str


class NewsSearchResponse(BaseModel):
    query: str
    articles: list[NewsArticleResponse]


class NewsErrorResponse(BaseModel):
    message: str
