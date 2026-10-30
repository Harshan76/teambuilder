from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.faculty_routes import faculty_bp
from routes.generation_routes import generation_bp
from routes.comparison_routes import comparison_bp
from routes.api_routes import api_bp
from routes.report_routes import report_bp

__all__ = [
    "auth_bp", "student_bp", "faculty_bp", "generation_bp",
    "comparison_bp", "api_bp", "report_bp"
]
