from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db
from models.entities import User, StudentProfile
from services.auth_service import login_user, logout_user, get_current_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.query(User).filter_by(email=email).first()

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

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "student")
        student_id = request.form.get("student_id", "").strip()
        department = request.form.get("department", "Computer Science").strip()

        if not full_name or not email or not password:
            flash("All mandatory fields must be completed.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/register.html")

        db = get_db()
        if db.query(User).filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html")

        new_user = User(
            email=email,
            full_name=full_name,
            role=role if role in ["student", "faculty"] else "student"
        )
        new_user.set_password(password)
        db.add(new_user)
        db.flush()

        # If student, create initial profile
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
        flash("Registration successful! You may now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", current_user=get_current_user())

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("auth.login"))
