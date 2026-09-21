import uuid
from datetime import datetime

import pytest
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    Table,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.base import NAMING_CONVENTION, Base, uuid_pk

TEST_URL = "postgresql+asyncpg://u:p@localhost/scratch_test"
POSTGRES_MAX_IDENTIFIER_LENGTH = 63


def scratch_metadata() -> MetaData:
    # A scratch MetaData with the real convention: nothing is registered on Base,
    # and no domain model or migration is needed to exercise the convention.
    return MetaData(naming_convention=Base.metadata.naming_convention)


def postgres_dialect() -> Dialect:
    # Building an engine opens no connection; it only supplies the dialect.
    return create_async_engine(TEST_URL).sync_engine.dialect


def ddl_for(table: Table) -> str:
    """CREATE TABLE plus every CREATE INDEX for `table`, as PostgreSQL DDL."""
    dialect = postgres_dialect()
    statements = [str(CreateTable(table).compile(dialect=dialect))]
    statements += [
        str(CreateIndex(index).compile(dialect=dialect)) for index in table.indexes
    ]
    return "\n".join(statements)


def test_base_metadata_uses_the_naming_convention() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION


def test_single_column_constraints_and_indexes_get_deterministic_names() -> None:
    metadata = scratch_metadata()
    parent = Table("parent", metadata, Column("id", Integer, primary_key=True))
    child = Table(
        "child",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("parent.id")),
        Column("code", Integer, unique=True),
        Column("size", Integer, index=True),
    )

    ddl = ddl_for(child)

    assert parent.primary_key.name == "pk_parent"
    for name in ("pk_child", "fk_child_parent_id_parent", "uq_child_code"):
        assert f"CONSTRAINT {name}" in ddl
    assert "CREATE INDEX ix_child_size" in ddl


def test_composite_unique_constraints_are_named_after_every_column() -> None:
    membership = Table(
        "membership",
        scratch_metadata(),
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer),
        Column("workspace_id", Integer),
        Column("role", Integer),
        UniqueConstraint("user_id", "workspace_id"),
        # Shares its first column with the constraint above: must not collide.
        UniqueConstraint("user_id", "role"),
    )

    ddl = ddl_for(membership)

    assert "CONSTRAINT uq_membership_user_id_workspace_id UNIQUE" in ddl
    assert "CONSTRAINT uq_membership_user_id_role UNIQUE" in ddl


def test_composite_indexes_are_named_after_every_column() -> None:
    membership = Table(
        "membership",
        scratch_metadata(),
        Column("user_id", Integer),
        Column("workspace_id", Integer),
        Column("role", Integer),
    )
    Index(None, membership.c.user_id, membership.c.workspace_id)
    Index(None, membership.c.user_id, membership.c.role)

    ddl = ddl_for(membership)

    assert "CREATE INDEX ix_membership_user_id_workspace_id" in ddl
    assert "CREATE INDEX ix_membership_user_id_role" in ddl


def test_composite_foreign_keys_are_named_after_every_column() -> None:
    metadata = scratch_metadata()
    Table(
        "parent",
        metadata,
        Column("tenant_id", Integer, primary_key=True),
        Column("id", Integer, primary_key=True),
    )
    child = Table(
        "child",
        metadata,
        Column("tenant_id", Integer),
        Column("owner_id", Integer),
        ForeignKeyConstraint(
            ["tenant_id", "owner_id"], ["parent.tenant_id", "parent.id"]
        ),
    )

    assert "CONSTRAINT fk_child_tenant_id_owner_id_parent" in ddl_for(child)


def test_named_check_constraints_use_their_name_in_the_convention() -> None:
    child = Table(
        "child",
        scratch_metadata(),
        Column("size", Integer),
        CheckConstraint("size > 0", name="size_positive"),
    )

    assert "CONSTRAINT ck_child_size_positive CHECK (size > 0)" in ddl_for(child)


def test_unnamed_check_constraints_are_rejected() -> None:
    with pytest.raises(InvalidRequestError, match="explicitly named"):
        Table(
            "child",
            scratch_metadata(),
            Column("size", Integer),
            CheckConstraint("size > 0"),
        )


def test_long_generated_names_stay_valid_postgres_identifiers_and_deterministic() -> (
    None
):
    def build() -> Table:
        return Table(
            "workspace_membership_invitation_records",
            scratch_metadata(),
            Column("invited_workspace_identifier", Integer),
            Column("invited_user_email_address", Integer),
            Column("invitation_expiry_timestamp", Integer),
            UniqueConstraint(
                "invited_workspace_identifier",
                "invited_user_email_address",
                "invitation_expiry_timestamp",
            ),
        )

    first, second = ddl_for(build()), ddl_for(build())

    assert first == second
    constraint_name = first.split("CONSTRAINT ")[1].split(" ")[0]
    assert constraint_name.startswith("uq_workspace_membership_invitation_records")
    assert len(constraint_name) <= POSTGRES_MAX_IDENTIFIER_LENGTH


def test_datetime_columns_are_timezone_aware() -> None:
    mapped = Base.type_annotation_map[datetime]

    assert isinstance(mapped, DateTime)
    assert mapped.timezone is True


def test_uuid_pk_is_a_client_side_uuid4_primary_key() -> None:
    class ScratchBase(DeclarativeBase):
        metadata = MetaData(naming_convention=NAMING_CONVENTION)
        type_annotation_map = Base.type_annotation_map

    class Thing(ScratchBase):
        __tablename__ = "thing"

        id: Mapped[uuid.UUID] = uuid_pk()
        created_at: Mapped[datetime]

    column = Thing.__table__.c.id
    default = column.default

    assert column.primary_key
    assert isinstance(column.type, Uuid)
    assert column.server_default is None
    assert default is not None and default.is_callable
    generated = default.arg(None)
    assert isinstance(generated, uuid.UUID) and generated.version == 4
    created_at_type = Thing.__table__.c.created_at.type
    assert isinstance(created_at_type, DateTime) and created_at_type.timezone
