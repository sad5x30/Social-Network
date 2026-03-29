"""sosal?

Revision ID: 19bccba0a95e
Revises: 5e3e1ec2dbcc
Create Date: 2026-03-29 14:53:08.994245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '19bccba0a95e'
down_revision: Union[str, Sequence[str], None] = '5e3e1ec2dbcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    has_legacy_chats = "table_chats" in tables
    has_new_chats = "chats" in tables
    has_messages = "table_messages" in tables
    has_participants = "chat_participants" in tables

    if has_legacy_chats and not has_new_chats:
        op.rename_table("table_chats", "chats")
        has_new_chats = True

    if not has_new_chats:
        op.create_table(
            "chats",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        has_new_chats = True

    if not has_participants:
        op.create_table(
            "chat_participants",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("chat_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("joined_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["chat_id"], ["chats.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["table_users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if has_legacy_chats:
        chat_columns = {column["name"] for column in sa.inspect(bind).get_columns("chats")}

        if {"user1_id", "user2_id"}.issubset(chat_columns):
            op.execute(
                """
                INSERT INTO chat_participants (chat_id, user_id, joined_at)
                SELECT id, user1_id, created_at
                FROM chats
                """
            )
            op.execute(
                """
                INSERT INTO chat_participants (chat_id, user_id, joined_at)
                SELECT id, user2_id, created_at
                FROM chats
                WHERE user2_id <> user1_id
                """
            )

            unique_constraints = {
                constraint["name"]
                for constraint in sa.inspect(bind).get_unique_constraints("chats")
                if constraint["name"]
            }
            if "uq_chat_user_pair" in unique_constraints:
                op.drop_constraint("uq_chat_user_pair", "chats", type_="unique")

            op.drop_column("chats", "user1_id")
            op.drop_column("chats", "user2_id")

    if not has_messages:
        op.create_table(
            "table_messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("chat_id", sa.Integer(), nullable=False),
            sa.Column("sender_id", sa.Integer(), nullable=False),
            sa.Column("text", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["chat_id"], ["chats.id"]),
            sa.ForeignKeyConstraint(["sender_id"], ["table_users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_table_messages_chat_id"), "table_messages", ["chat_id"], unique=False)
        op.create_index(op.f("ix_table_messages_created_at"), "table_messages", ["created_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "table_messages" in tables:
        indexes = {index["name"] for index in inspector.get_indexes("table_messages")}
        if op.f("ix_table_messages_created_at") in indexes:
            op.drop_index(op.f("ix_table_messages_created_at"), table_name="table_messages")
        if op.f("ix_table_messages_chat_id") in indexes:
            op.drop_index(op.f("ix_table_messages_chat_id"), table_name="table_messages")
        op.drop_table("table_messages")

    if "chat_participants" in tables:
        op.drop_table("chat_participants")

    if "chats" in tables:
        op.drop_table("chats")
