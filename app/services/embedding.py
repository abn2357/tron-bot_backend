from sentence_transformers import SentenceTransformer


def embed_text(model: SentenceTransformer, text: str) -> list[float]:
    """Encode text into a 768-dim vector using bge-base-zh-v1.5."""
    return model.encode(text, normalize_embeddings=True).tolist()
