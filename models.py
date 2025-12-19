from pydantic import BaseModel, ConfigDict


class Chapter(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    idx: int
    name: str
    link: str

    path: str
    paragraphs: list[str]
    title: str


class BookInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    idx: str
    source: str
    book_name: str
    path: str

    chapters: list[Chapter]
