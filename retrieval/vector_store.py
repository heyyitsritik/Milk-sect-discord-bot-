"""
Milestone 7: vector database connection (Phase 7).

Uses Chroma in embedded mode — no separate server, just a local folder
on disk (per our Phase 7 recommendation: Chroma for prototyping, Qdrant
for production later, behind this same interface).

Chroma's default embedding model runs automatically the first time you
add or query text — we don't need to call a separate embedding API for
this milestone.
"""

import chromadb

from shared.logging import get_logger

logger = get_logger(__name__)

_CHROMA_PATH = "./data/chroma"
_COLLECTION_NAME = "conversations"

_client = None


def get_client():
    """Return a persistent Chroma client — a single shared instance, same
    pattern as our database connection."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=_CHROMA_PATH,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        logger.info("Connected to Chroma at %s", _CHROMA_PATH)
    return _client


def get_collection():
    """Return our one collection, creating it if it doesn't exist yet."""
    client = get_client()
    return client.get_or_create_collection(name=_COLLECTION_NAME)


def add_chunk(chunk_id: str, text: str, metadata: dict) -> None:
    """
    Store one piece of text (e.g., a conversation) as an embedded vector,
    along with metadata (per Phase 7: a bare vector match is useless
    without the original text and context alongside it).
    """
    collection = get_collection()
    collection.add(ids=[chunk_id], documents=[text], metadatas=[metadata])
    logger.info("Added chunk %s to vector store", chunk_id)


def search_similar(query_text: str, top_n: int = 3) -> dict:
    """Find the top_n most semantically similar stored chunks to query_text."""
    collection = get_collection()
    results = collection.query(query_texts=[query_text], n_results=top_n)
    return results


if __name__ == "__main__":
    # A small, predictable proof: store a few unrelated sentences, then
    # search for something that should match ONE of them by MEANING,
    # not by shared exact words.
    add_chunk("test1", "I am exhausted, need to sleep", {"topic": "tiredness"})
    add_chunk("test2", "The new gaming update has a lot of bugs", {"topic": "gaming"})
    add_chunk("test3", "Let's grab pizza for dinner tonight", {"topic": "food"})

    results = search_similar("so tired right now")
    logger.info("Query: 'so tired right now'")
    logger.info("Top match: %s", results["documents"][0][0])
    logger.info("Full results: %s", results)