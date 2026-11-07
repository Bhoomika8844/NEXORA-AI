
from app.retrieval.query_rewriter import rewrite_query
from app.vectorstore.chroma_store import search_chunks
from app.retrieval.reranker import rerank_chunks
from app.generation.generator import generate_answer


def rewrite_node(state):
    original_query = state["query"]
    rewritten_query = rewrite_query(original_query)

    print("Original Query:", original_query)
    print("Rewritten Query:", rewritten_query)

    return {"rewritten_query": rewritten_query}


def retrieval_node(state):
    candidate_chunks = search_chunks(
        query=state["rewritten_query"],
        top_k=min(state["top_k"] * 3, 10),
        document_id=state["document_id"]
    )

    print("Hybrid Search Results:", len(candidate_chunks))

    return {"retrieved_chunks": candidate_chunks}


def reranking_node(state):
    reranked_chunks = rerank_chunks(
        query=state["rewritten_query"],
        retrieved_chunks=state["retrieved_chunks"],
        top_k=state["top_k"]
    )

    print("Reranked Results:", len(reranked_chunks))

    return {"reranked_chunks": reranked_chunks}


def generation_node(state):
    result = generate_answer(
        query=state["query"],
        retrieved_chunks=state["reranked_chunks"]
    )

    print("Answer Generated Successfully")

    return {
        "answer": result["answer"],
        "sources": result["sources"]
    }
