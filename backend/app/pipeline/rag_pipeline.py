from app.pipeline.rag_graph import rag_graph


def answer_question(
    query: str,
    top_k: int = 3,
    document_id: str | None = None
):
    if not query or not query.strip():
        raise ValueError("Question cannot be empty.")

    initial_state = {
        "query": query.strip(),
        "rewritten_query": "",
        "document_id": document_id,
        "top_k": top_k,
        "retrieved_chunks": [],
        "reranked_chunks": [],
        "answer": "",
        "sources": []
    }

    result = rag_graph.invoke(initial_state)

    return {
        "query": query,
        "answer": result["answer"],
        "sources": result["sources"],
        "total_sources": len(result["sources"])
    }