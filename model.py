from typing import List   # 类型提示


class Book:
    id: str
    name: str
    slug: str
    user: str

    def __init__(self, id, name, slug, user) -> None:
        self.id: str = id
        self.name: str = name
        self.slug: str = slug
        self.user: str = user


class Doc:
    id: str
    uuid: str
    parent_uuid: str
    title: str
    url: str
    book: Book
    parents: List

    def __init__(self, id, uuid, parent_uuid, title, url, book, parents) -> None:
        self.id: str = id
        self.uuid: str = uuid
        self.parent_uuid: str = parent_uuid
        self.title: str = title
        self.url: str = url
        self.book: Book = book
        self.parents: List = parents
