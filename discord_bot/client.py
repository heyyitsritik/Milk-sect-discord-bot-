"""
Milestone 14: read-only Discord connection.

Deliberately does ONLY ONE thing: connect, listen, log. No replying,
no engagement decision, no LLM call yet. This proves the live data
pipeline works before we add the riskier "bot talks back" piece in
the next milestone.
"""

import asyncio

import discord

from config.settings import settings
from response.engagement import should_respond
from response.delay import sample_reply_delay
from response.formatting import format_reply
from retrieval.retriever import retrieve_context
from prompting.assembler import assemble_prompt
from llm.client import generate_reply
from shared.logging import get_logger

logger = get_logger(__name__)

intents = discord.Intents.default()
intents.message_content = True  # matches the "Message Content Intent" toggle on the dev portal

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    logger.info("Connected to Discord as %s (id: %s)", client.user, client.user.id)
    logger.info("Listening on %d server(s)", len(client.guilds))


@client.event
async def on_message(message: discord.Message):
    # Don't process the bot's own messages — prevents an infinite reply loop.
    if message.author == client.user:
        return

    logger.info(
        "Message received — channel: #%s | author: %s | content: %r",
        message.channel, message.author, message.content,
    )

    mentions_bot = client.user in message.mentions
    is_reply_to_bot = (
        message.reference is not None
        and message.reference.resolved is not None
        and getattr(message.reference.resolved, "author", None) == client.user
    )

    if not should_respond(
        message_content=message.content,
        author_id=str(message.author.id),
        mentions_bot=mentions_bot,
        is_reply_to_bot=is_reply_to_bot,
    ):
        return

    # --- From here on, we're committed to generating a real reply ---
    context = retrieve_context(message.content, user_id=str(message.author.id))

    prompt = assemble_prompt(
        user_profile=context["user_profile"],
        relevant_memories=context["relevant_memories"],
        conversation_history=[],  # short-term history wiring comes in a later milestone
        current_message=f"{message.author.display_name}: {message.content}",
    )

    raw_reply = generate_reply(prompt)
    cleaned_reply = format_reply(raw_reply)

    delay_seconds = sample_reply_delay()
    logger.info("Waiting %.2fs before sending reply (human-like delay)", delay_seconds)
    await asyncio.sleep(delay_seconds)

    await message.channel.send(cleaned_reply)
    logger.info("Sent reply: %r", cleaned_reply)

if __name__ == "__main__":
    logger.info("Starting Discord client (read-only mode)...")
    client.run(settings.discord_bot_token)