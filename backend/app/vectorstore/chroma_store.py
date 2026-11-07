import re
import chromadb

from rank_bm25 import BM25Okapi

from app.embeddings.embedder import embed_chunks, embed_query


# -----------------------------------------
# ChromaDB Configuration
# -----------------------------------------

client = chromadb.PersistentClient(path="data/chroma_db")

collection = client.get_or_create_collection(
    name="document_chunks"
)


# -----------------------------------------
# Text Tokenization for BM25
# -----------------------------------------

def tokenize_text(text: str):
    """
    Convert text into lowercase tokens.
    Preserves technical terms such as:
    Python, PostgreSQL, REST-API, etc.
    """
    return re.findall(r"\b[\w.-]+\b", text.lower())


# -----------------------------------------
# Store Document Chunks
# -----------------------------------------

def store_chunks(chunks, document_id):

    if not chunks:
        return 0

    embeddings = embed_chunks(chunks)

    ids = [
        f"{document_id}_chunk_{chunk['chunk_id']}"
        for chunk in chunks
    ]

    documents = [
        chunk["text"]
        for chunk in chunks
    ]

    metadatas = [
        {
            "document_id": document_id,
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"]
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

    return len(ids)


# -----------------------------------------
# Semantic Search using ChromaDB
# -----------------------------------------

def search_semantic_chunks(
    query,
    top_k=3,
    document_id=None
):

    query_vector = embed_query(query)

    search_filter = None

    if document_id:
        search_filter = {
            "document_id": document_id
        }

    # Get matching document count
    stored_data = collection.get(
        where=search_filter,
        include=["documents"]
    )

    total_chunks = len(stored_data["ids"])

    if total_chunks == 0:
        return []

    search_count = min(top_k, total_chunks)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=search_count,
        where=search_filter,
        include=["documents", "metadatas", "distances"]
    )

    retrieved_chunks = []

    for i in range(len(results["ids"][0])):

        retrieved_chunks.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return retrieved_chunks


# -----------------------------------------
# Keyword Search using BM25
# -----------------------------------------

def search_keyword_chunks(
    query,
    top_k=3,
    document_id=None
):

    search_filter = None

    if document_id:
        search_filter = {
            "document_id": document_id
        }

    # Retrieve stored document chunks
    stored_data = collection.get(
        where=search_filter,
        include=["documents", "metadatas"]
    )

    documents = stored_data["documents"]
    metadatas = stored_data["metadatas"]
    ids = stored_data["ids"]

    if not documents:
        return []

    # Tokenize document chunks
    tokenized_documents = [
        tokenize_text(document)
        for document in documents
    ]

    # Remove empty documents from the BM25 corpus
    valid_indices = [
        i for i, tokens in enumerate(tokenized_documents)
        if tokens
    ]

    if not valid_indices:
        return []

    valid_tokens = [
        tokenized_documents[i]
        for i in valid_indices
    ]

    # Create BM25 index
    bm25 = BM25Okapi(valid_tokens)

    # Tokenize user query
    tokenized_query = tokenize_text(query)

    if not tokenized_query:
        return []

    # Calculate keyword relevance scores
    scores = bm25.get_scores(tokenized_query)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

    retrieved_chunks = []

    for index in ranked_indices:

        score = float(scores[index])

        # Ignore chunks with no keyword relevance
        if score <= 0:
            continue

        original_index = valid_indices[index]

        retrieved_chunks.append({
            "id": ids[original_index],
            "text": documents[original_index],
            "metadata": metadatas[original_index],
            "bm25_score": score
        })

        if len(retrieved_chunks) >= top_k:
            break

    return retrieved_chunks


# -----------------------------------------
# Reciprocal Rank Fusion (RRF)
# -----------------------------------------

def reciprocal_rank_fusion(
    semantic_results,
    keyword_results,
    top_k=3,
    rrf_constant=60
):

    combined_results = {}

    # Process semantic search rankings
    for rank, chunk in enumerate(semantic_results, start=1):

        chunk_id = chunk["id"]

        if chunk_id not in combined_results:
            combined_results[chunk_id] = {
                **chunk,
                "rrf_score": 0.0,
                "retrieval_methods": []
            }

        combined_results[chunk_id]["rrf_score"] += (
            1 / (rrf_constant + rank)
        )

        combined_results[chunk_id]["retrieval_methods"].append(
            "semantic"
        )

    # Process BM25 keyword rankings
    for rank, chunk in enumerate(keyword_results, start=1):

        chunk_id = chunk["id"]

        if chunk_id not in combined_results:
            combined_results[chunk_id] = {
                **chunk,
                "rrf_score": 0.0,
                "retrieval_methods": []
            }

        combined_results[chunk_id]["rrf_score"] += (
            1 / (rrf_constant + rank)
        )

        combined_results[chunk_id]["retrieval_methods"].append(
            "keyword"
        )

    # Sort by combined RRF score
    ranked_results = sorted(
        combined_results.values(),
        key=lambda chunk: chunk["rrf_score"],
        reverse=True
    )

    return ranked_results[:top_k]


# -----------------------------------------
# Hybrid Search
# -----------------------------------------

def search_chunks(
    query,
    top_k=3,
    document_id=None
):

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k < 1 or top_k > 10:
        raise ValueError("top_k must be between 1 and 10.")

    # Retrieve a wider candidate set before fusion
    total_chunks = len(
        collection.get(
            where={"document_id": document_id}
            if document_id else None,
            include=["documents"]
        )["ids"]
    )

    if total_chunks == 0:
        return []

    candidate_k = min(
        max(top_k * 3, 10),
        total_chunks
    )

    # Step 1: Semantic retrieval
    semantic_results = search_semantic_chunks(
        query=query,
        top_k=candidate_k,
        document_id=document_id
    )

    # Step 2: Keyword retrieval
    keyword_results = search_keyword_chunks(
        query=query,
        top_k=candidate_k,
        document_id=document_id
    )

    # Step 3: Combine rankings using RRF
    hybrid_results = reciprocal_rank_fusion(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        top_k=top_k
    )

    return hybrid_results