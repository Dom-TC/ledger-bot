"""Script to migrate from the CSVs produced by the old airtable database to the new SQLite models."""

import csv
import logging
import logging.config
import os
import random
from contextlib import contextmanager
from datetime import datetime
from math import ceil
from pathlib import Path
from typing import Generator, List

import typer
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ledger_bot.models import (
    BotMessage,
    Member,
    MessageType,
    ReactionRole,
    Reminder,
    Transaction,
)

# Load environment variables from .env
load_dotenv()

# Set the log level based on the environment variable
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {log_level}")

# Configure logging
logging.config.fileConfig(fname="log.conf", disable_existing_loggers=False)
logging.getLogger().setLevel(numeric_level)
logging.getLogger("apscheduler.scheduler").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)

if os.getenv("LOG_TO_FILE") == "false":
    logging.info("LOG_TO_FILE is false, removing FileHandlers")
    file_handlers = (
        handler
        for handler in logging.root.handlers
        if isinstance(handler, logging.FileHandler)
    )
    for handler in file_handlers:
        logging.root.removeHandler(handler)
elif os.getenv("LOG_FOLDER_PATH") is not None:
    logging.info(
        f"Updating logging FileHandler path to `{os.getenv('LOG_FOLDER_PATH')}`"
    )

    file_handlers = (
        handler
        for handler in logging.root.handlers
        if isinstance(handler, logging.FileHandler)
    )
    for handler in file_handlers:
        handler.stream.close()
        handler.baseFilename = os.path.abspath(f"{os.getenv('LOG_FOLDER_PATH')}/log")
        handler.stream = handler._open()

log = logging.getLogger(__name__)

db_url = os.getenv("DATABASE_URL")
engine = create_engine(f"sqlite:///{db_url}")
SessionLocal = sessionmaker(bind=engine)


@contextmanager
def get_session():
    """Context manager for a clean session per batch."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:  # noqa: B902
        session.rollback()
        log.error(f"Rolled back due to: {e}")
        raise
    finally:
        session.close()


def sample_from_generator(gen: Generator, sample_size: int) -> List:
    """Randomly sample `sample_size` items from a generator."""
    reservoir = []
    for i, item in enumerate(gen):
        if i < sample_size:
            reservoir.append(item)
        else:
            r = random.randint(0, i)
            if r < sample_size:
                reservoir[r] = item
    return reservoir


member_old_to_new_ids = {}
transaction_old_to_new_ids = {}
bot_message_old_to_new_ids = {}
reminder_old_to_new_ids = {}


# ------------------------------------
# ---------- REACTION ROLES ----------
# ------------------------------------


def load_reaction_roles(csv_path: Path) -> Generator[ReactionRole]:
    """Generator to return a ReactionRole object from a csv."""
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield ReactionRole(
                server_id=int(row["server_id"]),
                message_id=int(row["message_id"]),
                reaction_name=row["reaction_name"].strip(),
                role_id=int(row["role_id"]),
                role_name=row["role_name"].strip(),
                reaction_bytecode=row.get("reaction_bytecode")
                or row["reaction_name"]
                .strip()
                .encode("unicode-escape")
                .decode("ASCII"),
                bot_id=row.get("bot_id") or None,
            )


def migrate_reaction_roles(csv_folder: str):
    """Migrate ReactionRoles."""
    csv_path = Path(csv_folder, "reaction_roles.csv")

    with get_session() as session:
        _i = 0
        for _i, reaction_role in enumerate(load_reaction_roles(csv_path)):
            session.add(reaction_role)

        row_count = _i + 1
        min_sample_size = ceil(row_count * 0.3) if ceil(row_count * 0.3) > 3 else 3
        max_sample_size = ceil(row_count * 0.75)

        samples: List[ReactionRole] = sample_from_generator(
            load_reaction_roles(csv_path),
            random.randint(min_sample_size, max_sample_size),
        )

        for sample in samples:
            match = (
                session.query(ReactionRole)
                .filter_by(
                    server_id=sample.server_id,
                    message_id=sample.message_id,
                    reaction_name=sample.reaction_name,
                    role_id=sample.role_id,
                )
                .one_or_none()
            )

            if match is None:
                log.error(
                    f"Validation failed for sampled row: "
                    f"server_id={sample.server_id}, message_id={sample.message_id}, "
                    f"reaction_name={sample.reaction_name}, role_id={sample.role_id}"
                )

                raise ValueError("Sample validation failed. Aborting migration.")

        log.info(f"Added {row_count} reaction roles, validated {len(samples)}")


# ------------------------------------
# -------------- MEMBERS -------------
# ------------------------------------


class MigrationMember(Member):
    def __init__(self, airtable_id: int, **kwargs):
        self.airtable_id = airtable_id
        super().__init__(**kwargs)


def load_members(csv_path: Path) -> Generator[MigrationMember]:
    """Generator to return a MigrationMember object from a csv."""
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield MigrationMember(
                username=row["username"].strip(),
                discord_id=int(row["discord_id"]),
                nickname=row["nickname"].strip() or None,
                bot_id=row["bot_id"].strip() or "MigrationBot",
                airtable_id=int(row["row_id"]),
            )


def migrate_members(csv_folder: str):
    """Migrate Member."""
    csv_path = Path(csv_folder, "members.csv")

    with get_session() as session:
        _i = 0
        for _i, member in enumerate(load_members(csv_path)):
            session.add(member)
            session.flush()
            db_row = (
                session.query(MigrationMember)
                .filter_by(
                    username=member.username,
                    discord_id=member.discord_id,
                    nickname=member.nickname,
                    bot_id=member.bot_id,
                )
                .one()
            )

            member_old_to_new_ids[member.airtable_id] = db_row.id

        row_count = _i + 1
        min_sample_size = ceil(row_count * 0.3) if ceil(row_count * 0.3) > 3 else 3
        max_sample_size = ceil(row_count * 0.75)

        samples: List[MigrationMember] = sample_from_generator(
            load_members(csv_path), random.randint(min_sample_size, max_sample_size)
        )

        for sample in samples:
            match: MigrationMember | None = (
                session.query(MigrationMember)
                .filter_by(
                    username=sample.username,
                    discord_id=sample.discord_id,
                    nickname=sample.nickname,
                    bot_id=sample.bot_id,
                )
                .one_or_none()
            )

            if match is None:
                log.error(
                    f"Validation failed for sampled row: "
                    f"username={sample.username}, discord_id={sample.discord_id}, "
                    f"nickname={sample.nickname}, bot_id={sample.bot_id}"
                )

                raise ValueError("Sample validation failed. Aborting migration.")

        log.info(f"Added {row_count} members, validated {len(samples)}")


# ------------------------------------
# ------------ TRANSACTION -----------
# ------------------------------------


class MigrationTransaction(Transaction):
    def __init__(self, seller_discord_id: int, buyer_discord_id: int, **kwargs):
        self.seller_discord_id = seller_discord_id
        self.buyer_discord_id = buyer_discord_id
        super().__init__(**kwargs)


def load_transaction(csv_path: Path) -> Generator[MigrationTransaction]:
    """Generator to return a MigrationTransaction object from a csv."""
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield MigrationTransaction(
                display_id=int(row["row_id"]),
                seller_id=member_old_to_new_ids[int(row["seller_id"])],
                buyer_id=member_old_to_new_ids[int(row["buyer_id"])],
                wine=row["wine"].strip(),
                price=float(row["price"][1:]),
                sale_approved=1 if row["sale_approved"] == "checked" else 0,
                buyer_delivered=1 if row["buyer_marked_delivered"] == "checked" else 0,
                seller_delivered=(
                    1 if row["seller_marked_delivered"] == "checked" else 0
                ),
                buyer_paid=1 if row["buyer_marked_paid"] == "checked" else 0,
                seller_paid=1 if row["seller_marked_paid"] == "checked" else 0,
                cancelled=1 if row["cancelled"] == "checked" else 0,
                creation_date=(
                    datetime.strptime(row["creation_date"].strip(), "%Y-%m-%d %H:%M")
                    if row["creation_date"].strip()
                    else None
                ),
                approved_date=(
                    datetime.strptime(row["approved_date"].strip(), "%Y-%m-%d %H:%M")
                    if row["approved_date"].strip()
                    else None
                ),
                paid_date=(
                    datetime.strptime(row["paid_date"].strip(), "%Y-%m-%d %H:%M")
                    if row["paid_date"].strip()
                    else None
                ),
                delivered_date=(
                    datetime.strptime(row["delivered_date"].strip(), "%Y-%m-%d %H:%M")
                    if row["delivered_date"].strip()
                    else None
                ),
                cancelled_date=(
                    datetime.strptime(row["cancelled_date"].strip(), "%Y-%m-%d %H:%M")
                    if row["cancelled_date"].strip()
                    else None
                ),
                bot_id=row["bot_id"].strip() or "MigrationBot",
                seller_discord_id=int(row["seller_discord_id"]),
                buyer_discord_id=int(row["buyer_discord_id"]),
            )


def migrate_transactions(csv_folder: str):
    """Migrate Transaction."""
    csv_path = Path(csv_folder, "wines.csv")

    with get_session() as session:
        _i = 0
        for _i, transaction in enumerate(load_transaction(csv_path)):
            session.add(transaction)
            session.flush()
            db_row = (
                session.query(MigrationTransaction)
                .filter_by(
                    seller_id=transaction.seller_id,
                    buyer_id=transaction.buyer_id,
                    wine=transaction.wine,
                    price=transaction.price,
                    sale_approved=transaction.sale_approved,
                    buyer_delivered=transaction.buyer_delivered,
                    seller_delivered=transaction.seller_delivered,
                    buyer_paid=transaction.buyer_paid,
                    seller_paid=transaction.seller_paid,
                    cancelled=transaction.cancelled,
                    creation_date=transaction.creation_date,
                    approved_date=transaction.approved_date,
                    paid_date=transaction.paid_date,
                    delivered_date=transaction.delivered_date,
                    cancelled_date=transaction.cancelled_date,
                    bot_id=transaction.bot_id,
                )
                .order_by(MigrationTransaction.id.desc())
                .first()
            )

            if db_row:
                transaction_old_to_new_ids[transaction.display_id] = db_row.id

        row_count = _i + 1
        min_sample_size = ceil(row_count * 0.3) if ceil(row_count * 0.3) > 3 else 3
        max_sample_size = ceil(row_count * 0.75)

        samples: List[MigrationTransaction] = sample_from_generator(
            load_transaction(csv_path), random.randint(min_sample_size, max_sample_size)
        )

        for sample in samples:
            match: MigrationTransaction | None = (
                session.query(MigrationTransaction)
                .filter_by(
                    id=transaction_old_to_new_ids[sample.display_id],
                    seller_id=sample.seller_id,
                    buyer_id=sample.buyer_id,
                    wine=sample.wine,
                    price=sample.price,
                    sale_approved=sample.sale_approved,
                    buyer_delivered=sample.buyer_delivered,
                    seller_delivered=sample.seller_delivered,
                    buyer_paid=sample.buyer_paid,
                    seller_paid=sample.seller_paid,
                    cancelled=sample.cancelled,
                    creation_date=sample.creation_date,
                    approved_date=sample.approved_date,
                    paid_date=sample.paid_date,
                    delivered_date=sample.delivered_date,
                    cancelled_date=sample.cancelled_date,
                    bot_id=sample.bot_id,
                )
                .one_or_none()
            )

            has_valid_relations = True

            if match:
                if match.seller.discord_id != sample.seller_discord_id:
                    has_valid_relations = False

                if match.buyer.discord_id != sample.buyer_discord_id:
                    has_valid_relations = False

            if match is None or has_valid_relations is False:
                log.error(
                    f"Validation failed for sampled row: "
                    f"seller_id={sample.seller_id}, buyer_id={sample.buyer_id}, "
                    f"sale_approved={sample.sale_approved}, buyer_delivered={sample.buyer_delivered}, "
                    f"seller_delivered={sample.seller_delivered}, buyer_paid={sample.buyer_paid}, "
                    f"seller_paid={sample.seller_paid}, cancelled={sample.cancelled}, "
                    f"creation_date={sample.creation_date}, approved_date={sample.approved_date}, "
                    f"paid_date={sample.paid_date}, delivered_date={sample.delivered_date}, "
                    f"cancelled_date={sample.cancelled_date}, bot_id={sample.bot_id}"
                )

                raise ValueError("Sample validation failed. Aborting migration.")

        log.info(f"Added {row_count} transactions, validated {len(samples)}")

        old_id, new_id = next(reversed(transaction_old_to_new_ids.items()))

        id_offset = old_id - new_id

        log.info(f"id_offset should be: {id_offset}")


# ------------------------------------
# ----------- BOT MESSAGES -----------
# ------------------------------------


class MigrationBotMessage(BotMessage):
    def __init__(
        self,
        airtable_id: int,
        seller_discord_id: int,
        buyer_discord_id: int,
        wine: str,
        **kwargs,
    ):
        self.airtable_id = airtable_id
        self.seller_discord_id = seller_discord_id
        self.buyer_discord_id = buyer_discord_id
        self.wine = wine
        super().__init__(**kwargs)


def load_bot_message(csv_path: Path) -> Generator[MigrationBotMessage]:
    """Generator to return a MigrationBotMessage object from a csv."""
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield MigrationBotMessage(
                message_id=int(row["bot_message_id"]),
                channel_id=int(row["channel_id"]),
                guild_id=int(row["guild_id"]),
                message_type=MessageType.TRANSACTION,
                transaction_id=transaction_old_to_new_ids.get(
                    int(row["transaction_id"]), 999
                ),
                event_id=None,
                creation_date=(
                    datetime.strptime(
                        row["message_creation_date"].strip(), "%Y-%m-%d %H:%M"
                    )
                    if row["message_creation_date"].strip()
                    else None
                ),
                bot_id=row["bot_id"].strip() or "MigrationBot",
                airtable_id=int(row["row_id"]),
                seller_discord_id=int(row["seller_discord_id"]),
                buyer_discord_id=int(row["buyer_discord_id"]),
                wine=row["wine"].strip(),
            )


def migrate_bot_messages(csv_folder: str):
    """Migrate BotMessage."""
    csv_path = Path(csv_folder, "bot_messages.csv")

    with get_session() as session:
        _i = 0
        for _i, bot_message in enumerate(load_bot_message(csv_path)):
            session.add(bot_message)
            session.flush()
            db_row = (
                session.query(MigrationBotMessage)
                .filter_by(
                    message_id=bot_message.message_id,
                    channel_id=bot_message.channel_id,
                    guild_id=bot_message.guild_id,
                    message_type=MessageType.TRANSACTION,
                    transaction_id=bot_message.transaction_id,
                    creation_date=bot_message.creation_date,
                    bot_id=bot_message.bot_id,
                )
                .order_by(MigrationBotMessage.id.desc())
                .first()
            )

            if db_row:
                bot_message_old_to_new_ids[bot_message.airtable_id] = db_row.id

        row_count = _i + 1
        min_sample_size = ceil(row_count * 0.3) if ceil(row_count * 0.3) > 3 else 3
        max_sample_size = ceil(row_count * 0.75)

        samples: List[MigrationBotMessage] = sample_from_generator(
            load_bot_message(csv_path), random.randint(min_sample_size, max_sample_size)
        )

        for sample in samples:
            match: MigrationBotMessage | None = (
                session.query(MigrationBotMessage)
                .filter_by(
                    id=bot_message_old_to_new_ids[sample.airtable_id],
                    message_id=sample.message_id,
                    channel_id=sample.channel_id,
                    guild_id=sample.guild_id,
                    transaction_id=sample.transaction_id,
                    creation_date=sample.creation_date,
                    bot_id=sample.bot_id,
                )
                .one_or_none()
            )

            has_valid_relations = True

            if match and match.transaction:
                if match.transaction.wine != sample.wine:
                    has_valid_relations = False

                if match.transaction.buyer.discord_id != sample.buyer_discord_id:
                    has_valid_relations = False

                if match.transaction.seller.discord_id != sample.seller_discord_id:
                    has_valid_relations = False

            if match is None or has_valid_relations is False:
                log.error(
                    f"Validation failed for sampled row: "
                    f"message_id={sample.message_id}, channel_id={sample.channel_id}, "
                    f"guild_id={sample.guild_id}, transaction_id={sample.transaction_id}, "
                    f"creation_date={sample.creation_date}, bot_id={sample.bot_id}"
                )

                raise ValueError("Sample validation failed. Aborting migration.")

        log.info(f"Added {row_count} bot messages, validated {len(samples)}")


# ------------------------------------
# ------------ REMINDERS -------------
# ------------------------------------


class MigrationReminder(Reminder):
    def __init__(self, airtable_id: int, discord_id: int, wine: str, **kwargs):
        self.airtable_id = airtable_id
        self.discord_id = discord_id
        self.wine = wine
        super().__init__(**kwargs)


def load_reminder(csv_path: Path) -> Generator[MigrationReminder]:
    """Generator to return a MigrationBotMessage object from a csv."""
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield MigrationReminder(
                reminder_date=(
                    datetime.strptime(row["date"].strip(), "%Y-%m-%d %H:%M")
                    if row["date"].strip()
                    else None
                ),
                member_id=member_old_to_new_ids[int(row["member_id"])],
                transaction_id=transaction_old_to_new_ids[int(row["transaction_id"])],
                category=row["status"].strip() if row["status"].strip() else None,
                bot_id=row["bot_id"].strip() or "MigrationBot",
                airtable_id=int(row["row_id"]),
                discord_id=int(row["discord_id"]),
                wine=row["wine"].strip(),
            )


def migrate_reminders(csv_folder: str):
    """Migrate Reminder."""
    csv_path = Path(csv_folder, "reminders.csv")

    with get_session() as session:
        _i = 0
        for _i, reminder in enumerate(load_reminder(csv_path)):
            session.add(reminder)
            session.flush()
            db_row = (
                session.query(MigrationReminder)
                .filter_by(
                    reminder_date=reminder.reminder_date,
                    member_id=reminder.member_id,
                    transaction_id=reminder.transaction_id,
                    category=reminder.category,
                    bot_id=reminder.bot_id,
                )
                .order_by(MigrationReminder.id.desc())
                .first()
            )

            if db_row:
                reminder_old_to_new_ids[reminder.airtable_id] = db_row.id

        row_count = _i + 1
        min_sample_size = (
            ceil(row_count * 0.3) if ceil(row_count * 0.3) > 3 else row_count
        )
        max_sample_size = ceil(row_count * 0.75)

        samples: List[MigrationReminder] = sample_from_generator(
            load_reminder(csv_path), random.randint(min_sample_size, max_sample_size)
        )

        for sample in samples:
            match: MigrationReminder | None = (
                session.query(MigrationReminder)
                .filter_by(
                    id=reminder_old_to_new_ids[sample.airtable_id],
                    reminder_date=sample.reminder_date,
                    member_id=sample.member_id,
                    transaction_id=sample.transaction_id,
                    category=sample.category,
                    bot_id=sample.bot_id,
                )
                .one_or_none()
            )

            has_valid_relations = True

            if match:
                if match.transaction.wine != sample.wine:
                    has_valid_relations = False

                if match.member.discord_id != sample.discord_id:
                    has_valid_relations = False

            if match is None or has_valid_relations is False:
                log.error(
                    f"Validation failed for sampled row: "
                    f"reminder_date={sample.reminder_date}, member_id={sample.member_id}, "
                    f"transaction_id={sample.transaction_id}, category={sample.category}, "
                    f"bot_id={sample.bot_id}"
                )

                raise ValueError("Sample validation failed. Aborting migration.")

        log.info(f"Added {row_count} reminders, validated {len(samples)}")


def main(csv_folder: str = "data/migrations"):
    """Migrate airtable data from provided csvs into the SQLite database.

    --csv-folder: the folder where the CSVs are stored
    """
    log.info(f"CSV folder: {csv_folder}")
    log.info("Starting data migration...")

    migrate_reaction_roles(csv_folder=csv_folder)
    migrate_members(csv_folder=csv_folder)
    migrate_transactions(csv_folder=csv_folder)
    migrate_bot_messages(csv_folder=csv_folder)
    migrate_reminders(csv_folder=csv_folder)

    log.info("All migrations complete.")


if __name__ == "__main__":
    typer.run(main)
