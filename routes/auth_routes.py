import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from database.db import get_db
from models.entities import User, StudentProfile
from services.auth_service import login_user, logout_user, get_current_user

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login endpoint.
    Retrieves existing user and verifies password hash.
    NEVER creates or inserts a new user.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("auth/login.html", current_user=get_current_user())

        db = get_db()
        try:
            # Query existing user only (Read-only)
            user = db.query(User).filter(func.lower(User.email) == email).first()

            if user and user.check_password(password):
                login_user(user)
                flash(f"Welcome back, {user.full_name}!", "success")
                if user.is_faculty():
                    return redirect(url_for("faculty.dashboard"))
                else:
                    return redirect(url_for("student.dashboard"))
            else:
                flash("Invalid email or password. Please verify credentials.", "danger")
                return render_template("auth/login.html", current_user=get_current_user())

        except SQLAlchemyError as se:
            db.rollback()
            logger.error(f"Database error during login for {email}: {se}")
            flash("A database error occurred during sign in. Please try again.", "danger")
            return render_template("auth/login.html", current_user=get_current_user())
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error during login for {email}: {e}")
            flash("An unexpected error occurred during sign in. Please try again.", "danger")
            return render_template("auth/login.html", current_user=get_current_user())

    return render_template("auth/login.html", current_user=get_current_user())

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Registration endpoint.
    Validates form input, pre-checks for existing email,
    and safely creates new user with hashed password.
    """
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "student").strip().lower()
        student_id = request.form.get("student_id", "").strip()
        department = request.form.get("department", "Computer Science").strip()

        # Validation: Required fields
        if not full_name or not email or not password:
            flash("All mandatory fields must be completed.", "danger")
            return render_template("auth/register.html", current_user=get_current_user())

        # Validation: Password match
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html", current_user=get_current_user())

        # Validation: Password minimum length
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/register.html", current_user=get_current_user())

        db = get_db()
        try:
            # 1. Pre-check: Verify email does not already exist before attempting INSERT
            existing_user = db.query(User).filter(func.lower(User.email) == email).first()
            if existing_user:
                flash("An account with this email address already exists. Please sign in instead.", "warning")
                return render_template("auth/register.html", current_user=get_current_user())

            # 2. Pre-check: If registering as student with a provided student ID, check for duplicates
            if role == "student" and student_id:
                existing_profile = db.query(StudentProfile).filter_by(student_id=student_id).first()
                if existing_profile:
                    flash(f"Student ID '{student_id}' is already registered to another account.", "danger")
                    return render_template("auth/register.html", current_user=get_current_user())

            # 3. Create the user entity with secure password hash
            new_user = User(
                email=email,
                full_name=full_name,
                role=role if role in ["student", "faculty"] else "student"
            )
            new_user.set_password(password)
            db.add(new_user)
            db.flush()

            # 4. If student, initialize profile
            if new_user.is_student():
                if not student_id:
                    student_id = f"STU-{new_user.id:04d}"
                profile = StudentProfile(
                    user_id=new_user.id,
                    student_id=student_id,
                    department=department or "Computer Science",
                    is_profile_complete=False
                )
                db.add(profile)

            db.commit()
            flash("Registration successful! You may now sign in with your credentials.", "success")
            return redirect(url_for("auth.login"))

        except IntegrityError as ie:
            db.rollback()
            logger.warning(f"IntegrityError during registration for {email}: {ie}")
            flash("An account with this email address or Student ID already exists. Please sign in instead.", "warning")
            return render_template("auth/register.html", current_user=get_current_user())
        except SQLAlchemyError as se:
            db.rollback()
            logger.error(f"SQLAlchemyError during registration for {email}: {se}")
            flash("A database error occurred during registration. Please try again.", "danger")
            return render_template("auth/register.html", current_user=get_current_user())
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error during registration for {email}: {e}")
            flash("An unexpected error occurred during registration. Please try again.", "danger")
            return render_template("auth/register.html", current_user=get_current_user())

    return render_template("auth/register.html", current_user=get_current_user())

@auth_bp.route("/logout")
def logout():
    """Logout endpoint. Clears session and redirects to login."""
    logout_user()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("auth.login"))
