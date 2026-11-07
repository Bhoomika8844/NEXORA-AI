
from typing import TypedDict


class RAGState(TypedDict):

    query: str

    rewritten_query: str

    document_id: str | None

    top_k: int

    retrieved_chunks: list

    reranked_chunks: list

    answer: str

    sources: list
