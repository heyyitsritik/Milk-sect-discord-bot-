"""
Milestone 9: the retriever (Phase 6 + Phase 7 combined).

CRITICAL design rule, enforced by the code structure itself, not just
a comment: profile lookup and similarity search are two separate calls.
Profile lookup NEVER goes through vector_store.py. Similarity search
NEVER touches profile_store.py. This function just combines their
two independent results.
"""

from memory.profiles.profile_store import get_profile
from retrieval.vector_store import search_similar
from shared.logging import get_logger

logger = get_logger(__name__)


def retrieve_context(incoming_message: str, user_id: str, top_n: int = 3) -> dict:
    """
    Gather everything the prompt-assembly step will eventually need:
      - relevant_memories: semantically similar past chunks (via Chroma)
      - user_profile: this specific person's known facts (via direct SQL lookup)

    These are fetched through two independent code paths on purpose.
    """
    logger.info("Retrieving context for user %s, message: %r", user_id, incoming_message)

    # Path 1: similarity search — has NO knowledge of which user is asking.
    similarity_results = search_similar(incoming_message, top_n=top_n)
    relevant_memories = similarity_results["documents"][0] if similarity_results["documents"] else []

    # Path 2: profile lookup — has NO knowledge of the message content at all.
    user_profile = get_profile(user_id)

    logger.info("Found %d relevant memories, profile present: %s", len(relevant_memories), user_profile is not None)

    return {
        "relevant_memories": relevant_memories,
        "user_profile": user_profile,
    }


if __name__ == "__main__":
    # Proof: u1 has a profile (from Milestone 8), and our vector store
    # (from Milestone 7) has tiredness/gaming/food sentences in it.
    # A tiredness-related message from u1 should return BOTH correctly.
    result = retrieve_context("i'm so sleepy today", user_id="u1")
    logger.info("--- Result ---")
    logger.info("Relevant memories: %s", result["relevant_memories"])
    logger.info("User profile: %s", result["user_profile"])