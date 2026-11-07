from sentence_transformers import CrossEncoder


# -----------------------------------------
# Cross-Encoder Configuration
# -----------------------------------------

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Load the model only when reranking is first requested
_reranker = None


def get_reranker():
    global _reranker

    if _reranker is None:
        print("Loading Cross-Encoder model...")

        _reranker = CrossEncoder(
            MODEL_NAME,
            device="cpu"
        )

        print("Cross-Encoder model loaded successfully.")

    return _reranker


# -----------------------------------------
# Cross-Encoder Reranking
# -----------------------------------------

def rerank_chunks(
    query: str,
    retrieved_chunks: list,
    top_k: int = 3
):
    if not query or not query.strip():
        raise ValueError("Question cannot be empty.")

    if not retrieved_chunks:
        return []

    # Load Cross-Encoder
    model = get_reranker()

    # Create question-document pairs
    pairs = []

    valid_chunks = []

    for chunk in retrieved_chunks:

        text = chunk.get("text", "")

        if not text or not text.strip():
            continue

        pairs.append((query, text))
        valid_chunks.append(chunk)

    if not pairs:
        return []

    # Calculate relevance scores
    scores = model.predict(
        pairs,
        batch_size=16,
        show_progress_bar=False
    )

    # Attach reranking scores
    reranked_chunks = []

    for chunk, score in zip(valid_chunks, scores):

        updated_chunk = chunk.copy()

        updated_chunk["rerank_score"] = float(score)

        reranked_chunks.append(updated_chunk)

    # Sort by Cross-Encoder relevance
    reranked_chunks.sort(
        key=lambda chunk: chunk["rerank_score"],
        reverse=True
    )

    return reranked_chunks[:top_k]