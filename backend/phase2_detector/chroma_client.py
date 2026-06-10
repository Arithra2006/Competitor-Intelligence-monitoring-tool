# backend/phase2_detector/chroma_client.py
# Stores and retrieves embeddings using ChromaDB
# ChromaDB runs locally — no server needed, no API key, completely free

import chromadb
from chromadb.config import Settings
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────
# CHROMADB SETUP
# ─────────────────────────────────────────

# Store ChromaDB data in backend/chroma_store/
CHROMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "chroma_store"
)

# Global client instance — initialize once
_client = None
_collection = None
COLLECTION_NAME = "competitor_embeddings"


def _get_collection():
    """
    Get or create ChromaDB collection.
    Initializes client and collection on first call.
    """
    global _client, _collection

    if _collection is not None:
        return _collection

    # Create storage directory if needed
    os.makedirs(CHROMA_PATH, exist_ok=True)

    # Initialize persistent ChromaDB client
    _client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Get or create collection
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # Use cosine similarity
    )

    print(f"✅ ChromaDB initialized — collection: {COLLECTION_NAME}")
    return _collection


# ─────────────────────────────────────────
# MAIN FUNCTIONS
# ─────────────────────────────────────────

def store_embedding(
    competitor_id: int,
    source: str,
    url: str,
    embedding: list[float],
    raw_text: str,
) -> str:
    """
    Store an embedding in ChromaDB.
    Each entry is uniquely identified by competitor_id + source.
    Overwrites previous embedding for same competitor + source.

    Args:
        competitor_id: ID of the competitor
        source: Data source ('website', 'careers', 'news', 'github')
        url: URL that was scraped
        embedding: Embedding vector (384 floats)
        raw_text: Raw text that was embedded

    Returns:
        Document ID used in ChromaDB
    """
    collection = _get_collection()

    # Unique ID per competitor + source combination
    doc_id = f"comp_{competitor_id}_{source}"

    # Metadata stored alongside embedding
    metadata = {
        "competitor_id": str(competitor_id),
        "source": source,
        "url": url,
        "text_length": str(len(raw_text)),
    }

    # Upsert — insert or update if exists
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[raw_text[:500]],  # Store preview only — full text in SQLite
        metadatas=[metadata],
    )

    return doc_id


def get_stored_embedding(competitor_id: int, source: str) -> dict | None:
    """
    Retrieve the previously stored embedding for a competitor + source.
    Returns None if no embedding exists yet (first crawl).

    Args:
        competitor_id: ID of the competitor
        source: Data source ('website', 'careers', 'news', 'github')

    Returns:
        Dict with embedding, metadata, and document preview — or None
    """
    collection = _get_collection()
    doc_id = f"comp_{competitor_id}_{source}"

    try:
        result = collection.get(
            ids=[doc_id],
            include=["embeddings", "metadatas", "documents"],
        )

        if not result["ids"]:
            return None

        return {
            "id": doc_id,
            "embedding": result["embeddings"][0],
            "metadata": result["metadatas"][0],
            "document_preview": result["documents"][0],
        }

    except Exception as e:
        print(f"⚠️  Could not retrieve embedding for {doc_id}: {e}")
        return None


def delete_embedding(competitor_id: int, source: str) -> bool:
    """
    Delete stored embedding for a competitor + source.
    Used when a competitor is removed from tracking.

    Returns:
        True if deleted, False if not found
    """
    collection = _get_collection()
    doc_id = f"comp_{competitor_id}_{source}"

    try:
        collection.delete(ids=[doc_id])
        print(f"🗑️  Deleted embedding: {doc_id}")
        return True
    except Exception as e:
        print(f"⚠️  Could not delete embedding {doc_id}: {e}")
        return False


def delete_all_embeddings_for_competitor(competitor_id: int) -> None:
    """
    Delete all embeddings for a competitor across all sources.
    Called when a competitor is fully removed.
    """
    sources = ["website", "careers", "news", "github", "reddit"]
    for source in sources:
        delete_embedding(competitor_id, source)


def get_collection_stats() -> dict:
    """
    Return stats about the ChromaDB collection.
    Useful for debugging and dashboard display.
    """
    collection = _get_collection()
    count = collection.count()
    return {
        "collection_name": COLLECTION_NAME,
        "total_embeddings": count,
        "storage_path": CHROMA_PATH,
    }


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from embedder import generate_embedding

    print("🧪 Testing ChromaDB client...\n")

    # Test texts — simulating two crawls of same page
    text_v1 = "Our platform provides analytics and reporting tools for teams."
    text_v2 = "Our AI-powered platform provides analytics, forecasting and reporting for teams."

    # Generate embeddings
    print("Generating embeddings...")
    emb_v1 = generate_embedding(text_v1)
    emb_v2 = generate_embedding(text_v2)
    print(f"✅ Embeddings generated — {len(emb_v1)} dimensions each")

    # Store first embedding (simulating first crawl)
    print("\nStoring first embedding (crawl 1)...")
    doc_id = store_embedding(
        competitor_id=1,
        source="website",
        url="https://notion.so",
        embedding=emb_v1,
        raw_text=text_v1,
    )
    print(f"✅ Stored with ID: {doc_id}")

    # Retrieve it
    print("\nRetrieving stored embedding...")
    stored = get_stored_embedding(competitor_id=1, source="website")
    if stored:
        print(f"✅ Retrieved — dimensions: {len(stored['embedding'])}")
        print(f"   Preview: {stored['document_preview']}")
        print(f"   Metadata: {stored['metadata']}")
    else:
        print("❌ Could not retrieve embedding")

    # Store second embedding (simulating second crawl — overwrite)
    print("\nStoring second embedding (crawl 2 — overwrite)...")
    store_embedding(
        competitor_id=1,
        source="website",
        url="https://notion.so",
        embedding=emb_v2,
        raw_text=text_v2,
    )
    print("✅ Overwritten with new embedding")

    # Collection stats
    print("\nCollection stats:")
    stats = get_collection_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")

    print("\n✅ ChromaDB test complete!")