"""
Milestone 11: LLM client (Phase 9).

A thin wrapper around the chosen provider's API. Every other part of
the project calls generate_reply() and never touches the OpenAI/Groq
client directly — that's what makes swapping providers later a change
to this ONE file, not a project-wide rewrite.
"""

from openai import OpenAI

from config.settings import settings
from shared.logging import get_logger

logger = get_logger(__name__)

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_api_base_url,
        )
        logger.info("LLM client initialized for %s", settings.llm_api_base_url)
    return _client


def generate_reply(prompt: str) -> str:
    """
    Send the assembled prompt to the LLM and return its reply as plain text.
    """
    client = get_client()
    logger.info("Sending prompt to LLM (%d characters)", len(prompt))

    response = client.chat.completions.create(
        model=settings.llm_model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )

    reply_text = response.choices[0].message.content
    logger.info("Received reply (%d characters): %r", len(reply_text), reply_text)
    return reply_text


if __name__ == "__main__":
    from prompting.assembler import assemble_prompt
    from retrieval.retriever import retrieve_context

    context = retrieve_context("i'm so sleepy today", user_id="u1")
    prompt = assemble_prompt(
        user_profile=context["user_profile"],
        relevant_memories=context["relevant_memories"],
        conversation_history=["sam: anyone else exhausted today"],
        current_message="ritik: i'm so sleepy today",
    )

    reply = generate_reply(prompt)
    print("=" * 60)
    print("LLM REPLY:", reply)
    print("=" * 60)