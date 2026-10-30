import os
import logging
from flask import Flask, redirect, url_for, render_template, jsonify
from config import Config
from database.db import db_manager
from services.auth_service import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Database & Create Tables
    db_manager.init_db(app, uri_override=config_class.get_database_uri() if hasattr(config_class, "get_database_uri") else None)
    db_manager.create_all()

    # Optional Auto-Seed for First-Time Railway Deployment
    if getattr(config_class, "AUTO_SEED", False):
        try:
            from database.seed_data import seed_database
            logger.info("AUTO_SEED=true detected. Seeding database...")
            seed_database()
        except Exception as e:
            logger.warning(f"Auto-seed encountered a non-critical notice: {e}")

    # Register Blueprints
    from routes import (
        auth_bp, student_bp, faculty_bp, generation_bp,
        comparison_bp, api_bp, report_bp
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(generation_bp)
    app.register_blueprint(comparison_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(report_bp)

    # Context Processor for Global Template Variables
    @app.context_processor
    def inject_user_and_status():
        user = get_current_user()
        return {
            "current_user": user,
            "db_type": db_manager.db_type,
            "db_status_message": db_manager.connection_status_message
        }

    # Production Health-Check Endpoints
    @app.route("/health")
    @app.route("/api/health")
    def health_check():
        from sqlalchemy import text
        db_status = "connected"
        http_code = 200
        try:
            db = db_manager.get_session()
            db.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {e}"
            http_code = 503

        return jsonify({
            "status": "healthy" if http_code == 200 else "degraded",
            "database": db_status,
            "database_type": getattr(db_manager, "db_type", "unknown"),
            "service": "AI Group Project Team Builder",
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "production" if not app.debug else "development"),
            "version": "1.0.0"
        }), http_code

    # Favicon endpoint to ensure clean browser requests without 404
    @app.route("/favicon.ico")
    def favicon():
        from flask import Response
        svg_favicon = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect width="100" height="100" rx="22" fill="#4f46e5"/>'
            '<path d="M50 18 L72 38 L60 38 L60 78 L40 78 L40 38 L28 38 Z" fill="#ffffff"/>'
            '<circle cx="50" cy="50" r="8" fill="#38bdf8"/>'
            '</svg>'
        )
        return Response(svg_favicon, mimetype="image/svg+xml")

    # Root route
    @app.route("/")
    def index():
        user = get_current_user()
        if user:
            if user.is_faculty():
                return redirect(url_for("faculty.dashboard"))
            else:
                return redirect(url_for("student.dashboard"))
        return redirect(url_for("auth.login"))

    # CLI Command to Seed Database: `flask seed-db`
    @app.cli.command("seed-db")
    def seed_db_command():
        """Initialize database with demonstration catalog and student cohort."""
        from database.seed_data import seed_database
        db_manager.create_all()
        seed_database()
        print("Database schema created and demo cohort seeded successfully.")

    # Custom Error Pages
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html"), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
