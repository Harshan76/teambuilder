from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db
from models.entities import StudentProfile, Project, TeamMember, Team
from services.auth_service import login_required, student_required, get_current_user
from services.student_service import StudentService
from services.project_service import ProjectService

student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    user = get_current_user()
    db = get_db()
    profile = StudentService.get_profile_by_user_id(user.id, session=db)
    
    is_complete, missing_reqs, completion_pct = False, [], 0
    if profile:
        is_complete, missing_reqs, completion_pct = StudentService.check_profile_completion(profile)

    projects = ProjectService.get_all_projects(status="Open", session=db)
    
    # Check if student is in any finalized team
    assigned_memberships = []
    if profile:
        assigned_memberships = db.query(TeamMember).join(Team).filter(
            TeamMember.profile_id == profile.id,
            Team.status == "Finalized"
        ).all()

    return render_template(
        "student/dashboard.html",
        current_user=user,
        profile=profile,
        is_complete=is_complete,
        missing_reqs=missing_reqs,
        completion_pct=completion_pct,
        projects=projects,
        assigned_memberships=assigned_memberships
    )

@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
@student_required
def profile_edit():
    user = get_current_user()
    db = get_db()
    profile = StudentService.get_profile_by_user_id(user.id, session=db)
    catalogs = StudentService.get_all_catalogs(session=db)

    if request.method == "POST":
        # Process form submission
        full_name = request.form.get("full_name", "").strip()
        student_id = request.form.get("student_id", "").strip()
        department = request.form.get("department", "").strip()
        experience_level = request.form.get("experience_level", "Beginner")
        experience_years = request.form.get("experience_years", 0.0)
        previous_projects = request.form.get("previous_projects_summary", "")
        collaboration_pref = request.form.get("collaboration_preference", "Flexible / Balanced")

        # Process skills: supports dynamic JSON payload, selected_skill_id lists, or individual inputs
        skills_input = []
        skills_json = request.form.get("skills_json")
        selected_ids = request.form.getlist("selected_skill_id")
        selected_profs = request.form.getlist("selected_skill_proficiency")

        if skills_json:
            try:
                import json
                parsed_skills = json.loads(skills_json)
                if isinstance(parsed_skills, list):
                    for item in parsed_skills:
                        s_id = item.get("id") or item.get("skill_id")
                        if s_id:
                            skills_input.append({
                                "skill_id": int(s_id),
                                "proficiency": max(1, min(5, int(item.get("proficiency", 3))))
                            })
            except Exception:
                pass

        if not skills_input and selected_ids:
            for idx, s_id in enumerate(selected_ids):
                if s_id and str(s_id).isdigit():
                    p_val = int(selected_profs[idx]) if idx < len(selected_profs) and str(selected_profs[idx]).isdigit() else 3
                    skills_input.append({
                        "skill_id": int(s_id),
                        "proficiency": max(1, min(5, p_val))
                    })

        if not skills_input:
            for s in catalogs["skills"]:
                prof_val = request.form.get(f"skill_{s.id}")
                if prof_val and str(prof_val).isdigit() and int(prof_val) > 0:
                    skills_input.append({"skill_id": s.id, "proficiency": int(prof_val)})

        # Process interests: multiselect checkboxes named interest_ids
        interest_ids = request.form.getlist("interest_ids")

        # Process availability slots: multiselect checkboxes named slot_ids
        slot_ids = request.form.getlist("slot_ids")

        # Process preferred roles: inputs role_pref_1, role_pref_2, role_pref_3
        preferred_roles = []
        for rank in [1, 2, 3]:
            r_val = request.form.get(f"role_rank_{rank}")
            if r_val:
                preferred_roles.append({"role_id": int(r_val), "preference_rank": rank})

        update_payload = {
            "full_name": full_name,
            "student_id": student_id,
            "department": department,
            "experience_level": experience_level,
            "experience_years": experience_years,
            "previous_projects_summary": previous_projects,
            "collaboration_preference": collaboration_pref,
            "skills": skills_input,
            "interest_ids": interest_ids,
            "slot_ids": slot_ids,
            "preferred_roles": preferred_roles
        }

        try:
            StudentService.update_profile(profile.id, update_payload, session=db)
            flash("Profile updated successfully! Completeness verified.", "success")
            return redirect(url_for("student.dashboard"))
        except Exception as e:
            db.rollback()
            flash(f"Error updating profile: {e}", "danger")

    # Current profile selections
    selected_skill_map = {ss.skill_id: ss.proficiency for ss in profile.skills} if profile else {}
    selected_interests = {si.interest_id for si in profile.interests} if profile else set()
    selected_slots = {sa.slot_id for sa in profile.availability} if profile else set()
    selected_roles = {spr.preference_rank: spr.role_id for spr in profile.preferred_roles} if profile else {}

    is_complete, missing_reqs, completion_pct = False, [], 0
    if profile:
        is_complete, missing_reqs, completion_pct = StudentService.check_profile_completion(profile)

    return render_template(
        "student/profile_edit.html",
        current_user=user,
        profile=profile,
        catalogs=catalogs,
        selected_skills=selected_skill_map,
        selected_interests=selected_interests,
        selected_slots=selected_slots,
        selected_roles=selected_roles,
        is_complete=is_complete,
        missing_reqs=missing_reqs,
        completion_pct=completion_pct
    )

@student_bp.route("/projects")
@login_required
@student_required
def projects_list():
    user = get_current_user()
    db = get_db()
    projects = ProjectService.get_all_projects(session=db)
    profile = StudentService.get_profile_by_user_id(user.id, session=db)
    return render_template("student/project_view.html", current_user=user, projects=projects, profile=profile)

@student_bp.route("/my-team/<int:project_id>")
@login_required
@student_required
def my_team(project_id):
    user = get_current_user()
    db = get_db()
    profile = StudentService.get_profile_by_user_id(user.id, session=db)
    project = ProjectService.get_project_by_id(project_id, session=db)

    if not profile or not project:
        flash("Invalid request or profile not found.", "warning")
        return redirect(url_for("student.dashboard"))

    # Find student's team membership in finalized teams
    membership = db.query(TeamMember).join(Team).filter(
        TeamMember.profile_id == profile.id,
        Team.project_id == project_id,
        Team.status == "Finalized"
    ).first()

    if not membership:
        flash("Teams for this project have not been finalized or published yet by the faculty.", "info")
        return redirect(url_for("student.dashboard"))

    team = membership.team
    teammates = team.members

    return render_template(
        "student/my_team.html",
        current_user=user,
        project=project,
        team=team,
        membership=membership,
        teammates=teammates
    )
