"""Placeholder database module.

The MVP stores logs in memory. Keeping this module in place makes it easy to
swap in SQLAlchemy with Neon PostgreSQL without changing route imports later.
"""

DATABASE_URL_ENV = "DATABASE_URL"
