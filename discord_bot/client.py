"""
Milestone 14/15/15.5/16: full Discord connection.

Connects, listens, saves every live message, decides whether to
respond, generates a reply when appropriate, and runs a periodic
background ingestion pass — all on one event loop.
"""

import asyncio

import discord

from config.settings import settings
from response.engagement import should_respond, mark_conversation_active
from response.delay import sample_reply_delay
from response.formatting import format_reply
from retrieval.retriever import retrieve_context
from prompting.assembler import assemble_prompt
from llm.client import generate_reply
from storage.db import get_connection
from ingestion.cleaning.normalize import clean_message_text
from ingestion.cleaning.reconstruct import reconstruct_conversations
from ingestion.analysis.style_stats import run_style_analysis
from shared.logging import get_logger

logger = get_logger(__name__)

BACKGROUND_INTERVAL_SECONDS = 120  # run every 2 minutes for testing; tune later


def save_live_message(message: discord.Message) -> None:
    """
    Persist one live Discord message into our database — the live-data
    equivalent of Milestone 2's importer, run automatically per message
    instead of from a JSON file.
    """
    connection = get_connection()
    try:
        connection.execute(
            "INSERT OR IGNORE INTO users (user_id, current_username, is_bot, is_deleted_account) VALUES (?, ?, ?, FALSE)",
            (str(message.author.id), message.author.display_name, message.author.bot),
        )
        connection.execute(
            "INSERT OR IGNORE INTO channels (channel_id, channel_name) VALUES (?, ?)",
            (str(message.channel.id), str(message.channel)),
        )

        reply_to_id = None
        if message.reference is not None:
            reply_to_id = str(message.reference.message_id)

        cleaned_content = clean_message_text(message.content)
        message_source = "BOT" if message.author.bot else "USER"

        connection.execute(
            """
            INSERT OR IGNORE INTO messages (
                message_id, author_id, channel_id, reply_to_message_id,
                content, content_type, message_source, sent_at
            )
            VALUES (?, ?, ?, ?, ?, 'TEXT', ?, ?)
            """,
            (
                str(message.id),
                str(message.author.id),
                str(message.channel.id),
                reply_to_id,
                cleaned_content,
                message_source,
                message.created_at.isoformat(),
            ),
        )
        connection.commit()
    finally:
        connection.close()
    
def get_recent_channel_history(channel_id: str, limit: int = 6) -> list[str]:
    """
    Fetch the last `limit` messages in this channel, formatted as
    "username: content" strings, oldest first — the actual short-term
    memory layer from Phase 6/8, now wired in for real.
    """
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT m.content, u.current_username
            FROM messages m
            JOIN users u ON m.author_id = u.user_id
            WHERE m.channel_id = ? AND m.content IS NOT NULL AND m.content != ''
            ORDER BY m.sent_at DESC
            LIMIT ?
            """,
            (channel_id, limit),
        ).fetchall()
        # We fetched newest-first (for an efficient LIMIT), but a
        # conversation should READ oldest-first — so reverse it.
        rows.reverse()
        return [f"{username}: {content}" for content, username in rows]
    finally:
        connection.close()


async def background_ingestion_loop():
    """
    Periodically reconstruct conversations and refresh stats from
    whatever real messages have accumulated — decoupled from the live
    reply loop, per Phase 11's worker pattern.
    """
    await client.wait_until_ready()
    while not client.is_closed():
        logger.info("Background worker: running ingestion pass...")
        try:
            reconstruct_conversations()
            run_style_analysis()
        except Exception:
            logger.exception("Background ingestion pass failed — will retry next cycle")
        await asyncio.sleep(BACKGROUND_INTERVAL_SECONDS)


intents = discord.Intents.default()
intents.message_content = True  # matches the "Message Content Intent" toggle on the dev portal


class PersonaBotClient(discord.Client):
    async def setup_hook(self):
        # discord.py calls this automatically once the client is starting up —
        # the correct, supported place to launch a background task, unlike
        # trying to access client.loop before run() has started anything.
        self.loop.create_task(background_ingestion_loop())


client = PersonaBotClient(intents=intents)


@client.event
async def on_ready():
    logger.info("Connected to Discord as %s (id: %s)", client.user, client.user.id)
    logger.info("Listening on %d server(s)", len(client.guilds))


@client.event
async def on_message(message: discord.Message):
    save_live_message(message)

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

    history = get_recent_channel_history(str(message.channel.id))

    prompt = assemble_prompt(
        user_profile=context["user_profile"],
        relevant_memories=context["relevant_memories"],
        conversation_history=history,
        current_message=f"{message.author.display_name}: {message.content}",
    )
    
    raw_reply = generate_reply(prompt)
    cleaned_reply = format_reply(raw_reply)

    delay_seconds = sample_reply_delay()
    logger.info("Waiting %.2fs before sending reply (human-like delay)", delay_seconds)
    await asyncio.sleep(delay_seconds)

    await message.channel.send(cleaned_reply)
    logger.info("Sent reply: %r", cleaned_reply)
    mark_conversation_active(str(message.author.id))


if __name__ == "__main__":
    logger.info("Starting Discord client (full loop + background worker)...")
    client.run(settings.discord_bot_token)