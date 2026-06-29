"""
Milestone 14: read-only Discord connection.

Deliberately does ONLY ONE thing: connect, listen, log. No replying,
no engagement decision, no LLM call yet. This proves the live data
pipeline works before we add the riskier "bot talks back" piece in
the next milestone.
"""

import discord

from config.settings import settings
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
    # Don't log the bot's own future messages once it starts sending them.
    if message.author == client.user:
        return

    logger.info(
        "Message received — channel: #%s | author: %s | content: %r",
        message.channel, message.author, message.content,
    )


if __name__ == "__main__":
    logger.info("Starting Discord client (read-only mode)...")
    client.run(settings.discord_bot_token)