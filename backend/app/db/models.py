"""SQLite-backed persistence tables are created in app.db.database.init_db.

The current MVP uses Python's stdlib sqlite3 to avoid adding a dependency while
keeping the storage boundary ready for a future SQLAlchemy/PostgreSQL swap.
"""
