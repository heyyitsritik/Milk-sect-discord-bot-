-- ============================================================
-- Discord Persona Bot — Database Schema (Phase 3 / Milestone 1)
-- ============================================================
-- Order matters: a table can only reference (via FOREIGN KEY) a table
-- that already exists. That's why USERS, CHANNELS come before MESSAGES,
-- and MESSAGES comes before REACTIONS/ATTACHMENTS/MENTIONS.

-- One row per person or bot who has ever sent a message.
CREATE TABLE IF NOT EXISTS users (
    user_id            TEXT PRIMARY KEY,
    current_username   TEXT NOT NULL,
    is_bot             BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted_account BOOLEAN NOT NULL DEFAULT FALSE
);

-- One row per Discord channel.
CREATE TABLE IF NOT EXISTS channels (
    channel_id   TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL
);

-- One row per thread. Threads belong to a parent channel and
-- (usually) know which message spawned them.
CREATE TABLE IF NOT EXISTS threads (
    thread_id               TEXT PRIMARY KEY,
    parent_channel_id       TEXT NOT NULL,
    spawned_from_message_id TEXT,
    FOREIGN KEY (parent_channel_id) REFERENCES channels (channel_id)
);

-- The centerpiece: every message ever sent.
CREATE TABLE IF NOT EXISTS messages (
    message_id          TEXT PRIMARY KEY,
    author_id            TEXT NOT NULL,
    channel_id            TEXT NOT NULL,
    thread_id              TEXT,
    reply_to_message_id     TEXT,
    content                  TEXT,
    content_type              TEXT NOT NULL DEFAULT 'TEXT',
    message_source             TEXT NOT NULL DEFAULT 'USER',
    conversation_id              TEXT,
    sent_at                        TIMESTAMP NOT NULL,
    edited_at                       TIMESTAMP,
    is_deleted                       BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (author_id) REFERENCES users (user_id),
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id),
    FOREIGN KEY (thread_id) REFERENCES threads (thread_id),
    FOREIGN KEY (reply_to_message_id) REFERENCES messages (message_id)
);

-- Many reactions can belong to one message, and one user can react
-- to many messages — hence its own table, not a column on messages.
CREATE TABLE IF NOT EXISTS reactions (
    message_id TEXT NOT NULL,
    user_id    TEXT NOT NULL,
    emoji      TEXT NOT NULL,
    PRIMARY KEY (message_id, user_id, emoji),
    FOREIGN KEY (message_id) REFERENCES messages (message_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- One message can have multiple attachments.
CREATE TABLE IF NOT EXISTS attachments (
    attachment_id TEXT PRIMARY KEY,
    message_id     TEXT NOT NULL,
    url             TEXT NOT NULL,
    content_type     TEXT,
    FOREIGN KEY (message_id) REFERENCES messages (message_id)
);

-- One message can mention multiple users or roles.
CREATE TABLE IF NOT EXISTS mentions (
    message_id     TEXT NOT NULL,
    target_user_id  TEXT NOT NULL,
    mention_type     TEXT NOT NULL DEFAULT 'user',
    PRIMARY KEY (message_id, target_user_id),
    FOREIGN KEY (message_id) REFERENCES messages (message_id),
    FOREIGN KEY (target_user_id) REFERENCES users (user_id)
);

-- One row per user, holding distilled semantic-memory facts (Phase 6).
-- Deliberately separate from the vector store — profile lookups are
-- always a direct, keyed SELECT by user_id, never a similarity search.
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id     TEXT PRIMARY KEY,
    facts_json  TEXT NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);