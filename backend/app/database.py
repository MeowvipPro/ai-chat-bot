from urllib.parse import quote_plus
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()


def _build_database_url() -> str:
    db_type = settings.DB_TYPE.lower()
    if db_type == "mysql":
        password = quote_plus(settings.DB_PASSWORD)
        return (
            f"mysql+pymysql://{settings.DB_USER}:{password}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
    elif db_type == "mssql":
        driver = quote_plus(settings.MSSQL_DRIVER)
        password = quote_plus(settings.DB_PASSWORD)
        return (
            f"mssql+pyodbc://{settings.DB_USER}:{password}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            f"?driver={driver}&TrustServerCertificate=yes"
        )
    elif db_type == "sqlite":
        return f"sqlite:///{settings.SQLITE_PATH}"
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}. Use mysql, sqlite, or mssql.")


def _create_engine():
    url = _build_database_url()
    kwargs = {"pool_pre_ping": True}
    if settings.DB_TYPE.lower() == "sqlite":
        kwargs = {"connect_args": {"check_same_thread": False}}
    else:
        kwargs["pool_recycle"] = 3600
    return create_engine(url, **kwargs)


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Enable WAL mode and foreign keys for SQLite
if settings.DB_TYPE.lower() == "sqlite":
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db():
    """Create all tables (useful for SQLite or first-time setup)."""
    import app.models  # noqa: F401 — ensure models are imported
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
