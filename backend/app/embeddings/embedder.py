
from sentence_transformers import SentenceTransformer


# Load the embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def embed_chunks(chunks):
    """
    Convert document chunks into numerical vectors.
    """

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return embeddings.tolist()


def embed_query(query):
    """
    Convert a user's question into a numerical vector.
    """

    embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    return embedding.tolist()
