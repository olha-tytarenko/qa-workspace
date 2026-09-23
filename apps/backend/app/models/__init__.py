"""Model registry.

Every ORM model module must be imported here, and nowhere else. This package is
imported by `migrations/env.py`, which is what makes Alembic autogenerate and
`alembic check` see the models. A model that is not imported here does not exist
as far as migrations are concerned.

Models inherit `Base` from `app.db.base` and use `uuid_pk()` for primary keys.
"""

from app.models.user import User

__all__ = ["User"]
