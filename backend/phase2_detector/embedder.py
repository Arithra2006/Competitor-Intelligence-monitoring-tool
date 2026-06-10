# backend/phase2_detector/embedder.py
# Generates text embeddings using Sentence Transformers
# Runs locally — no API key needed, completely free
# Model downloads once (~90MB) and caches locally

from sentence_transformers import SentenceTransformer
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────
# MODEL SETUP
# ─────────────────────────────────────────

# all-MiniLM-L6-v2 is the best balance of:
# - Speed: very fast on CPU
# - Size: ~90MB download
# - Quality: excellent for semantic similarity
# Downloads automatically on first run, cached locally after
MODEL_NAME = "all-MiniLM-L6-v2"

# Global model instance — load once, reuse across all calls
_model = None


def _get_model() -> SentenceTransformer:
    """
    Load model once and cache it globally.
    Avoids reloading on every embedding call.
    """
    global _model
    if _model is None:
        print(f"📥 Loading embedding model: {MODEL_NAME}")
        print("   (First run downloads ~90MB — cached after that)")
        _model = SentenceTransformer(MODEL_NAME)
        print(f"✅ Embedding model loaded: {MODEL_NAME}")
    return _model


# ─────────────────────────────────────────
# MAIN EMBEDDING FUNCTION
# ─────────────────────────────────────────

def generate_embedding(text: str) -> list[float]:
    """
    Generate a semantic embedding vector for a text string.
    Returns a list of floats (384 dimensions for MiniLM).

    Args:
        text: Raw text to embed (page content, news, etc.)

    Returns:
        List of 384 floats representing the text semantically
    """
    if not text or not text.strip():
        print("⚠️  Empty text passed to embedder — returning zero vector")
        return [0.0] * 384

    # Truncate very long texts — model has token limit
    # MiniLM handles ~512 tokens (~2000 chars) well
    text = _truncate_text(text, max_chars=8000)

    model = _get_model()

    # Generate embedding
    embedding = model.encode(text, convert_to_numpy=True)

    # Convert numpy array to plain Python list for JSON storage
    return embedding.tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts at once.
    More efficient than calling generate_embedding() in a loop.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    model = _get_model()

    # Truncate each text
    truncated = [_truncate_text(t, max_chars=8000) for t in texts]

    # Batch encode — much faster than one by one
    embeddings = model.encode(truncated, convert_to_numpy=True, batch_size=32)

    return [e.tolist() for e in embeddings]


def compute_cosine_similarity(embedding1: list[float], embedding2: list[float]) -> float:
    """
    Compute cosine similarity between two embedding vectors.
    Returns a float between 0.0 and 1.0.
    1.0 = identical, 0.0 = completely different.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    # Handle zero vectors
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = np.dot(vec1, vec2) / (norm1 * norm2)

    # Clamp to [0, 1] range — floating point can give tiny negatives
    return float(np.clip(similarity, 0.0, 1.0))


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _truncate_text(text: str, max_chars: int = 8000) -> str:
    """
    Truncate text to max_chars.
    Cuts at word boundary where possible.
    """
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]

    # Try to cut at last space to avoid mid-word cut
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]

    return truncated


def embedding_to_str(embedding: list[float]) -> str:
    """Convert embedding list to comma-separated string for SQLite storage."""
    return ",".join(str(x) for x in embedding)


def str_to_embedding(embedding_str: str) -> list[float]:
    """Convert comma-separated string back to embedding list."""
    if not embedding_str:
        return []
    return [float(x) for x in embedding_str.split(",")]


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("🧪 Testing embedder...\n")

    # Test 1 — basic embedding
    text1 = "Our platform provides analytics and reporting tools."
    text2 = "Our AI-powered platform provides analytics, forecasting and reporting."
    text3 = "We sell office furniture and ergonomic chairs."

    print("Generating embeddings...")
    emb1 = generate_embedding(text1)
    emb2 = generate_embedding(text2)
    emb3 = generate_embedding(text3)

    print(f"\nEmbedding dimensions: {len(emb1)}")

    # Test 2 — similarity scores
    sim_12 = compute_cosine_similarity(emb1, emb2)
    sim_13 = compute_cosine_similarity(emb1, emb3)
    sim_23 = compute_cosine_similarity(emb2, emb3)

    print(f"\n--- SIMILARITY SCORES ---")
    print(f"Text1 vs Text2 (similar): {sim_12:.4f} → {'✅ Similar' if sim_12 > 0.8 else '🔄 Different'}")
    print(f"Text1 vs Text3 (different): {sim_13:.4f} → {'✅ Similar' if sim_13 > 0.8 else '🔄 Different'}")
    print(f"Text2 vs Text3 (different): {sim_23:.4f} → {'✅ Similar' if sim_23 > 0.8 else '🔄 Different'}")

    # Test 3 — batch embedding
    print(f"\n--- BATCH EMBEDDING TEST ---")
    texts = [text1, text2, text3]
    batch_embeddings = generate_embeddings_batch(texts)
    print(f"Batch size: {len(batch_embeddings)}")
    print(f"Each vector: {len(batch_embeddings[0])} dimensions")

    # Test 4 — string conversion
    print(f"\n--- STRING CONVERSION TEST ---")
    emb_str = embedding_to_str(emb1)
    emb_back = str_to_embedding(emb_str)
    match = len(emb_back) == len(emb1)
    print(f"String conversion: {'✅ OK' if match else '❌ Failed'}")

    print("\n✅ Embedder test complete!")