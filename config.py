import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    # Flask Secret Key
    SECRET_KEY = os.getenv("SECRET_KEY", "academic-team-builder-secret-key-2026")
    BASE_DIR = BASE_DIR
    
    # Port configuration for Railway / Cloud environments
    PORT = int(os.getenv("PORT", 5000))
    
    # ML Models directory
    ML_MODEL_DIR = BASE_DIR / "ml_models"
    ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # MySQL Database Settings (Supports standard names, Aiven, and Railway/Render injected variables)
    MYSQL_HOST = os.getenv("MYSQL_HOST") or os.getenv("MYSQLHOST") or os.getenv("AIVEN_HOST") or "localhost"
    MYSQL_PORT = int(os.getenv("MYSQL_PORT") or os.getenv("MYSQLPORT") or os.getenv("AIVEN_PORT") or 3306)
    MYSQL_USER = os.getenv("MYSQL_USER") or os.getenv("MYSQLUSER") or os.getenv("AIVEN_USER") or "root"
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD") or os.getenv("AIVEN_PASSWORD") or ""
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE") or os.getenv("AIVEN_DATABASE") or "ai_team_builder"
    
    # Database URL overrides (Render/Railway/Aiven injects DATABASE_URL, MYSQL_URL, or AIVEN_MYSQL_URL)
    DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL") or os.getenv("AIVEN_MYSQL_URL")
    
    # Auto-seed trigger for first-time production deployment
    AUTO_SEED = os.getenv("AUTO_SEED", "false").lower() in ("true", "1", "yes")

    @classmethod
    def get_database_uri(cls):
        """
        Determines the appropriate SQLAlchemy database URI.
        1. If DATABASE_URL or MYSQL_URL is provided, ensures PyMySQL driver dialect (mysql+pymysql://).
        2. If discrete MYSQL_* or MYSQL* variables are configured, builds the connection string.
        3. Falls back to local SQLite only when running in development with no database configured.
        """
        raw_url = cls.DATABASE_URL
        if raw_url:
            # Railway/Heroku provides mysql:// URI, but SQLAlchemy 2.0 requires mysql+pymysql://
            if raw_url.startswith("mysql://"):
                raw_url = raw_url.replace("mysql://", "mysql+pymysql://", 1)
            # Ensure utf8mb4 encoding is specified
            if "charset=" not in raw_url and "mysql+pymysql://" in raw_url:
                separator = "&" if "?" in raw_url else "?"
                raw_url = f"{raw_url}{separator}charset=utf8mb4"
            return raw_url
        
        # Build MySQL connection string from individual variables
        if cls.MYSQL_USER and (cls.MYSQL_HOST != "localhost" or cls.MYSQL_PASSWORD or os.getenv("MYSQLHOST") or os.getenv("MYSQL_HOST")):
            pwd = f":{cls.MYSQL_PASSWORD}" if cls.MYSQL_PASSWORD else ""
            mysql_uri = f"mysql+pymysql://{cls.MYSQL_USER}{pwd}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}?charset=utf8mb4"
            return mysql_uri
        
        # Default local dev fallback
        sqlite_path = cls.BASE_DIR / "ai_team_builder.db"
        return f"sqlite:///{sqlite_path.as_posix()}"

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    # Use in-memory SQLite for testing to ensure isolation and speed
    DATABASE_URL = "sqlite:///:memory:"

    @classmethod
    def get_database_uri(cls):
        return "sqlite:///:memory:"
