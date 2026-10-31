from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db, db_manager
from models.entities import Project, StudentProfile, ModelRun, Team, TeamGenerationRun, Skill, Role
from services.auth_service import login_required, faculty_required, get_current_user
from services.student_service import StudentService
from services.project_service import ProjectService
from ml.cluster_engine import StudentClusterEngine
from ml.feature_pipeline import StudentFeaturePipeline

faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")

@faculty_bp.route("/dashboard")
@login_required
@faculty_required
def dashboard():
    user = get_current_user()
    db = get_db()

    # Overview statistics
    total_students = db.query(StudentProfile).count()
    complete_profiles = db.query(StudentProfile).filter_by(is_profile_complete=True).count()
    total_projects = db.query(Project).count()
    active_runs = db.query(TeamGenerationRun).count()
    finalized_teams = db.query(Team).filter_by(status="Finalized").count()

    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    latest_model_run = db.query(ModelRun).order_by(ModelRun.trained_at.desc()).first()

    return render_template(
        "faculty/dashboard.html",
        current_user=user,
        total_students=total_students,
        complete_profiles=complete_profiles,
        total_projects=total_projects,
        active_runs=active_runs,
        finalized_teams=finalized_teams,
        projects=projects,
        latest_model_run=latest_model_run,
        db_status=db_manager.connection_status_message,
        db_type=db_manager.db_type
    )

@faculty_bp.route("/students")
@login_required
@faculty_required
def students_list():
    user = get_current_user()
    db = get_db()

    query = request.args.get("q")
    department = request.args.get("department")
    experience = request.args.get("experience")
    complete_only = request.args.get("complete_only") == "1"

    students = StudentService.get_all_students(
        query=query,
        department=department,
        experience=experience,
        complete_only=complete_only,
        session=db
    )

    # Department filter options
    departments = [d[0] for d in db.query(StudentProfile.department).distinct().all() if d[0]]

    return render_template(
        "faculty/students_list.html",
        current_user=user,
        students=students,
        departments=departments,
        current_query=query or "",
        current_dept=department or "",
        current_exp=experience or "",
        complete_only=complete_only
    )

@faculty_bp.route("/students/<int:profile_id>")
@login_required
@faculty_required
def student_detail(profile_id):
    user = get_current_user()
    db = get_db()
    profile = StudentService.get_profile_by_id(profile_id, session=db)
    if not profile:
        flash("Student profile not found.", "warning")
        return redirect(url_for("faculty.students_list"))

    is_complete, missing, pct = StudentService.check_profile_completion(profile)
    return render_template(
        "faculty/student_detail.html",
        current_user=user,
        profile=profile,
        is_complete=is_complete,
        missing=missing,
        completion_pct=pct
    )

@faculty_bp.route("/projects")
@login_required
@faculty_required
def projects_list():
    user = get_current_user()
    db = get_db()
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return render_template("faculty/projects_list.html", current_user=user, projects=projects)

@faculty_bp.route("/projects/new", methods=["GET", "POST"])
@login_required
@faculty_required
def project_create():
    user = get_current_user()
    db = get_db()
    catalogs = StudentService.get_all_catalogs(session=db)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        domain = request.form.get("domain", "").strip()
        description = request.form.get("description", "").strip()
        desired_team_size = int(request.form.get("desired_team_size", 4))
        min_team_size = int(request.form.get("min_team_size", 3))
        max_team_size = int(request.form.get("max_team_size", 5))
        experience_req = request.form.get("experience_level_required", "Any")

        # Parse skills
        skill_ids = request.form.getlist("required_skill_id")
        req_skills = []
        for s_id in skill_ids:
            if s_id:
                min_p = int(request.form.get(f"skill_prof_{s_id}", 2))
                is_mand = request.form.get(f"skill_mand_{s_id}") == "on"
                p_wt = float(request.form.get(f"skill_weight_{s_id}", 1.0))
                req_skills.append({
                    "skill_id": int(s_id),
                    "min_proficiency": min_p,
                    "is_mandatory": is_mand,
                    "priority_weight": p_wt
                })

        # Parse roles
        role_ids = request.form.getlist("required_role_id")
        req_roles = []
        for r_id in role_ids:
            if r_id:
                cnt = int(request.form.get(f"role_count_{r_id}", 1))
                req_roles.append({
                    "role_id": int(r_id),
                    "count_needed": cnt
                })

        payload = {
            "title": title,
            "domain": domain,
            "description": description,
            "desired_team_size": desired_team_size,
            "min_team_size": min_team_size,
            "max_team_size": max_team_size,
            "experience_level_required": experience_req,
            "required_skills": req_skills,
            "required_roles": req_roles
        }

        try:
            new_proj = ProjectService.create_project(payload, creator_id=user.id, session=db)
            flash(f"Academic Project '{new_proj.title}' created successfully!", "success")
            return redirect(url_for("faculty.projects_list"))
        except Exception as e:
            db.rollback()
            flash(f"Error creating project: {e}", "danger")

    return render_template(
        "faculty/project_form.html",
        current_user=user,
        catalogs=catalogs,
        project=None
    )

@faculty_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
@faculty_required
def project_edit(project_id):
    user = get_current_user()
    db = get_db()
    project = ProjectService.get_project_by_id(project_id, session=db)
    if not project:
        flash("Project not found.", "warning")
        return redirect(url_for("faculty.projects_list"))

    catalogs = StudentService.get_all_catalogs(session=db)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        domain = request.form.get("domain", "").strip()
        description = request.form.get("description", "").strip()
        desired_team_size = int(request.form.get("desired_team_size", 4))
        min_team_size = int(request.form.get("min_team_size", 3))
        max_team_size = int(request.form.get("max_team_size", 5))
        experience_req = request.form.get("experience_level_required", "Any")
        status = request.form.get("status", project.status)

        # Parse skills
        skill_ids = request.form.getlist("required_skill_id")
        req_skills = []
        for s_id in skill_ids:
            if s_id:
                min_p = int(request.form.get(f"skill_prof_{s_id}", 2))
                is_mand = request.form.get(f"skill_mand_{s_id}") == "on"
                p_wt = float(request.form.get(f"skill_weight_{s_id}", 1.0))
                req_skills.append({
                    "skill_id": int(s_id),
                    "min_proficiency": min_p,
                    "is_mandatory": is_mand,
                    "priority_weight": p_wt
                })

        # Parse roles
        role_ids = request.form.getlist("required_role_id")
        req_roles = []
        for r_id in role_ids:
            if r_id:
                cnt = int(request.form.get(f"role_count_{r_id}", 1))
                req_roles.append({
                    "role_id": int(r_id),
                    "count_needed": cnt
                })

        payload = {
            "title": title,
            "domain": domain,
            "description": description,
            "desired_team_size": desired_team_size,
            "min_team_size": min_team_size,
            "max_team_size": max_team_size,
            "experience_level_required": experience_req,
            "status": status,
            "required_skills": req_skills,
            "required_roles": req_roles
        }

        try:
            ProjectService.update_project(project.id, payload, session=db)
            flash(f"Project '{project.title}' updated successfully!", "success")
            return redirect(url_for("faculty.projects_list"))
        except Exception as e:
            db.rollback()
            flash(f"Error updating project: {e}", "danger")

    return render_template(
        "faculty/project_form.html",
        current_user=user,
        catalogs=catalogs,
        project=project
    )

@faculty_bp.route("/model-status")
@login_required
@faculty_required
def model_status():
    user = get_current_user()
    db = get_db()

    total_students = db.query(StudentProfile).count()
    complete_profiles = db.query(StudentProfile).filter_by(is_profile_complete=True).count()
    model_runs = db.query(ModelRun).order_by(ModelRun.trained_at.desc()).limit(5).all()
    latest_run = model_runs[0] if model_runs else None

    # Load fitted model if present on disk or reconstruct summaries from persistent DB
    cluster_engine = StudentClusterEngine.load()
    cluster_summaries = {}
    if cluster_engine and cluster_engine.cluster_summaries:
        cluster_summaries = cluster_engine.cluster_summaries
    elif latest_run and latest_run.features_json:
        try:
            cluster_summaries = json.loads(latest_run.features_json)
        except Exception:
            cluster_summaries = {}

    # Readiness indicators
    is_ready = complete_profiles >= 4
    warning = None
    if not is_ready:
        warning = f"Current complete cohort has {complete_profiles} students. Minimum 4 required for K-Means statistical clustering."

    return render_template(
        "faculty/model_status.html",
        current_user=user,
        total_students=total_students,
        complete_profiles=complete_profiles,
        model_runs=model_runs,
        latest_run=latest_run,
        cluster_engine=cluster_engine,
        cluster_summaries=cluster_summaries,
        is_ready=is_ready,
        warning=warning
    )
