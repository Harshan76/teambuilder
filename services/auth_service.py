from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
from database.db import get_db
from models.entities import User, StudentProfile

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    return db.query(User).filter_by(id=user_id).first()

def login_user(user):
    session.clear()
    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_role"] = user.role
    session["user_name"] = user.full_name

def logout_user():
    session.clear()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in with faculty credentials to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        if session.get("user_role") != "faculty":
            flash("Access denied: Faculty privileges required.", "danger")
            return redirect(url_for("student.dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access your student portal.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        if session.get("user_role") != "student":
            return redirect(url_for("faculty.dashboard"))
        return f(*args, **kwargs)
    return decorated_function
