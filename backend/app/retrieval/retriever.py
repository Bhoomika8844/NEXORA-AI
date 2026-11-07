
from app.vectorstore.chroma_store import search_chunks
from app.retrieval.reranker import rerank_chunks
from app.retrieval.query_rewriter import rewrite_query


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 3,
    document_id: str | None = None
):

    # Validate original question
    if not query or not query.strip():
        raise ValueError("Question cannot be empty.")

    if top_k < 1 or top_k > 10:
        raise ValueError("top_k must be between 1 and 10.")

    # Step 1: Rewrite the user's question
    rewritten_query = rewrite_query(query)

    print(f"Original Query: {query}")
    print(f"Rewritten Query: {rewritten_query}")

    # Step 2: Retrieve candidate chunks using Hybrid Search
    candidate_chunks = search_chunks(
        query=rewritten_query,
        top_k=min(top_k * 3, 30),
        document_id=document_id
    )

    # Step 3: Rerank candidates using Cross-Encoder
    reranked_chunks = rerank_chunks(
        query=rewritten_query,
        retrieved_chunks=candidate_chunks,
        top_k=top_k
    )

    return reranked_chunks
