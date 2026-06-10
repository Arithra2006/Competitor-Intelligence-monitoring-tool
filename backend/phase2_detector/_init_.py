# Phase 2 — Detector Package
# Generates embeddings, stores in ChromaDB,
# computes cosine similarity, filters meaningful changes only

from .embedder import generate_embedding
from .chroma_client import store_embedding, get_stored_embedding
from .similarity_checker import check_similarity, is_meaningful_change

_all_ = [
    "generate_embedding",
    "store_embedding",
    "get_stored_embedding",
    "check_similarity",
    "is_meaningful_change",
]