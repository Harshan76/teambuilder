import os
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from config import Config

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def init_db(self, app=None, uri_override=None):
        if getattr(self, "initialized", False) and not uri_override:
            return

        self.db_type = "unknown"
        self.connection_status_message = ""
        uri = uri_override or Config.get_database_uri()

        # Connect MySQL if configured
        if uri.startswith("mysql"):
            try:
                # Production-ready MySQL engine with connection pool recycling and ping
                engine_kwargs = {
                    "pool_pre_ping": True,
                    "pool_recycle": 300,
                    "connect_args": {"connect_timeout": 10}
                }
                test_engine = create_engine(uri, **engine_kwargs)
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self.engine = test_engine
                self.db_type = "mysql"
                self.connection_status_message = f"Connected to MySQL on {Config.MYSQL_HOST}:{Config.MYSQL_PORT} ({Config.MYSQL_DATABASE})"
                logger.info(self.connection_status_message)
            except Exception as e:
                # In production (Railway, explicit DATABASE_URL / MYSQL_URL / MYSQLHOST set), raise error instead of silent degrade
                is_prod = bool(
                    os.getenv("RAILWAY_ENVIRONMENT")
                    or os.getenv("FLASK_ENV") == "production"
                    or os.getenv("DATABASE_URL")
                    or os.getenv("MYSQL_URL")
                    or os.getenv("MYSQLHOST")
                )
                if is_prod:
                    logger.error(f"FATAL: Production MySQL connection failed ({e}). Aborting fallback to prevent data loss.")
                    raise RuntimeError(f"Production MySQL connection failed: {e}. Check your Railway MySQL environment variables.") from e
                
                # Local dev fallback only
                sqlite_path = Config.BASE_DIR / "ai_team_builder.db"
                fallback_uri = f"sqlite:///{sqlite_path.as_posix()}"
                logger.warning(f"MySQL connection failed ({e}). Falling back to local SQLite at {sqlite_path}")
                self.engine = create_engine(fallback_uri, connect_args={"check_same_thread": False})
                self.db_type = "sqlite"
                self.connection_status_message = f"Using local SQLite fallback"
        else:
            is_sqlite = uri.startswith("sqlite")
            connect_args = {"check_same_thread": False} if is_sqlite else {}
            self.engine = create_engine(uri, connect_args=connect_args)
            self.db_type = "sqlite" if is_sqlite else "other"
            self.connection_status_message = f"Connected to database: {self.db_type}"

        # Enable foreign keys for SQLite
        if self.db_type == "sqlite":
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.Session = scoped_session(self.session_factory)
        self.initialized = True

    def create_all(self):
        """Creates all tables declared in SQLAlchemy models safely."""
        from models import entities  # ensure models are imported
        Base.metadata.create_all(self.engine)

    def get_session(self):
        if not getattr(self, "initialized", False):
            self.init_db()
        return self.Session()

db_manager = DatabaseManager()

def get_db():
    return db_manager.get_session()
