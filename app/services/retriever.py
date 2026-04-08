from chromadb import Collection

from app.config import settings


def retrieve(collection: Collection, query_embedding: list[float]) -> list[str]:
    """Query Chroma for the most relevant document chunks."""
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=settings.retrieval.top_k,
        include=["documents", "distances"],
    )

    documents = results["documents"][0]
    distances = results["distances"][0]

    # Chroma returns L2 distances by default; lower = more similar.
    # Convert to a similarity-like score: similarity = 1 / (1 + distance)
    filtered = []
    for doc, dist in zip(documents, distances):
        score = 1.0 / (1.0 + dist)
        if score >= settings.retrieval.score_threshold:
            filtered.append(doc)

    return filtered
