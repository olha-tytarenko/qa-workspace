import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column

# Deterministic constraint and index names, so Alembic autogenerate and
# hand-written migrations can always refer to a constraint by a predictable name.
# Composite indexes, unique constraints and foreign keys include every
# participating column (`column_0_N_*`), so two of them starting with the same
# column cannot collide. Names longer than PostgreSQL's 63-character limit are
# truncated by SQLAlchemy deterministically.
# Check constraints must be named explicitly: their name is part of the result.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Every `Mapped[datetime]` column is `timestamptz`. Application code stores
    # and reads timezone-aware UTC values; naive datetimes are a bug.
    type_annotation_map = {datetime: DateTime(timezone=True)}


def uuid_pk() -> MappedColumn[uuid.UUID]:
    """Primary key for persisted entities: a UUIDv4 generated in Python.

    The default is deliberately client-side (`uuid.uuid4`), not a PostgreSQL
    `gen_random_uuid()` server default. Use it as
    `id: Mapped[uuid.UUID] = uuid_pk()`.
    """
    return mapped_column(primary_key=True, default=uuid.uuid4)
