"""Custom SQLAlchemy column types."""
from datetime import timezone
from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """A DateTime that stores naive UTC and always returns timezone-aware UTC.

    SQLite has no native timezone support, so storing naive UTC keeps the on-disk type
    unchanged (no migration needed) while every value read back is timezone-aware. That
    lets the whole app compare against datetime.now(timezone.utc) without ever mixing
    naive and aware datetimes.
    """
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)
