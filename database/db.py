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
                from sqlalchemy.engine.url import make_url
                parsed_url = make_url(uri)
                query_params = dict(parsed_url.query)

                # Robust handling of cloud MySQL (Aiven, Railway, AWS, etc.)
                # PyMySQL raises TypeError on '?ssl-mode=REQUIRED' in URL query parameters.
                # We strip it from query and configure PyMySQL's SSL connect_args properly.
                ssl_mode = query_params.pop("ssl-mode", None) or query_params.pop("ssl_mode", None)
                host_str = (parsed_url.host or "").lower()
                is_cloud_mysql = any(k in host_str for k in ["aivencloud.com", "railway.app", "amazonaws.com", "render.com", "azure.com"])
                enable_ssl = bool(
                    ssl_mode
                    or is_cloud_mysql
                    or os.getenv("MYSQL_SSL", "").lower() in ("true", "1", "required", "yes")
                )

                clean_url = parsed_url.set(query=query_params)

                connect_args = {"connect_timeout": 10}
                if enable_ssl:
                    ssl_dict = {"check_hostname": False}
                    ca_path = os.getenv("MYSQL_SSL_CA") or os.getenv("SSL_CA")
                    if ca_path and os.path.exists(ca_path):
                        ssl_dict["ca"] = ca_path
                    connect_args["ssl"] = ssl_dict

                # Production-ready MySQL engine with connection pool recycling and ping
                engine_kwargs = {
                    "pool_pre_ping": True,
                    "pool_recycle": 180,
                    "pool_size": int(os.getenv("MYSQL_POOL_SIZE", 10)),
                    "max_overflow": int(os.getenv("MYSQL_MAX_OVERFLOW", 20)),
                    "connect_args": connect_args
                }
                test_engine = create_engine(clean_url, **engine_kwargs)
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self.engine = test_engine
                self.db_type = "mysql"
                self.connection_status_message = f"Connected to MySQL on {parsed_url.host}:{parsed_url.port or 3306} ({parsed_url.database})"
                logger.info(self.connection_status_message)
            except Exception as e:
                # In production (Railway, explicit DATABASE_URL / MYSQL_URL / MYSQLHOST set), raise error instead of silent degrade
                is_prod = bool(
                    os.getenv("RAILWAY_ENVIRONMENT")
                    or os.getenv("RENDER")
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
        """Creates all tables declared in SQLAlchemy models safely and guarantees master catalogs exist."""
        from models import entities  # ensure models are imported
        Base.metadata.create_all(self.engine)
        try:
            from database.seed_data import ensure_master_catalogs
            session = self.get_session()
            ensure_master_catalogs(session=session)
            logger.info("Reference master catalogs verified and ensured.")
        except Exception as e:
            logger.warning(f"Could not ensure reference master catalogs during create_all: {e}")

    def get_session(self):
        if not getattr(self, "initialized", False):
            self.init_db()
        return self.Session()

    def remove_session(self):
        """Cleanly removes thread-local scoped session and releases connection to pool."""
        if getattr(self, "Session", None) is not None:
            try:
                self.Session.remove()
            except Exception as e:
                logger.warning(f"Error removing scoped session: {e}")

db_manager = DatabaseManager()

def get_db():
    return db_manager.get_session()
