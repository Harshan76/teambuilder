import json
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.db import get_db
from models.entities import (
    Project, StudentProfile, TeamGenerationRun, Team,
    TeamMember, RoleAssignment, EvaluationResult, Role
)
from services.auth_service import login_required, faculty_required, get_current_user
from services.student_service import StudentService
from services.project_service import ProjectService
from services.baseline_engine import RuleBasedTeamEngine
from services.role_recommender import RoleRecommender
from services.evaluation_service import EvaluationService
from ml.ml_team_engine import MLGuidedTeamEngine

generation_bp = Blueprint("generation", __name__, url_prefix="/generation")

@generation_bp.route("/<int:project_id>")
@login_required
@faculty_required
def project_generation_setup(project_id):
    user = get_current_user()
    db = get_db()
    project = ProjectService.get_project_by_id(project_id, session=db)
    if not project:
        flash("Project not found.", "warning")
        return redirect(url_for("faculty.projects_list"))

    eligible, ineligible = ProjectService.get_eligible_students(project.id, session=db)
    
    # Check existing generation runs for this project
    existing_runs = db.query(TeamGenerationRun).filter_by(project_id=project.id).order_by(TeamGenerationRun.created_at.desc()).all()

    return render_template(
        "faculty/generate_teams.html",
        current_user=user,
        project=project,
        eligible_students=eligible,
        ineligible_students=ineligible,
        default_weights=RuleBasedTeamEngine.DEFAULT_WEIGHTS,
        existing_runs=existing_runs
    )

@generation_bp.route("/<int:project_id>/baseline", methods=["POST"])
@login_required
@faculty_required
def run_baseline_generation(project_id):
    db = get_db()
    project = ProjectService.get_project_by_id(project_id, session=db)
    if not project:
        flash("Project not found.", "warning")
        return redirect(url_for("faculty.projects_list"))

    # Extract weights
    weights = {
        "technical_skill": float(request.form.get("weight_skill", 0.40)),
        "interest_domain": float(request.form.get("weight_interest", 0.20)),
        "experience": float(request.form.get("weight_experience", 0.15)),
        "availability": float(request.form.get("weight_availability", 0.15)),
        "preferred_role": float(request.form.get("weight_role", 0.10))
    }
    random_seed = int(request.form.get("random_seed", 42))

    eligible, ineligible = ProjectService.get_eligible_students(project.id, session=db)

    # Execute Baseline Generation
    res = RuleBasedTeamEngine.generate_teams(
        eligible_students=eligible,
        project=project,
        weights=weights,
        random_seed=random_seed
    )

    if not res.get("success"):
        flash(f"Baseline generation failed: {res.get('error')}", "danger")
        return redirect(url_for("generation.project_generation_setup", project_id=project.id))

    # Recommend Roles for each team
    all_roles = db.query(Role).all()
    for t_data in res["teams"]:
        RoleRecommender.recommend_roles_for_team(
            team_members=t_data["members"],
            project=project,
            available_roles=all_roles
        )

    # Evaluate observable metrics
    eval_metrics = EvaluationService.evaluate_generation(
        teams_data=res["teams"],
        project=project,
        total_eligible_count=len(eligible),
        runtime_seconds=res["runtime_seconds"],
        method="baseline"
    )

    # Persist in Database
    gen_run = TeamGenerationRun(
        project_id=project.id,
        method="baseline",
        weights_json=json.dumps(res["weights"]),
        random_seed=random_seed,
        n_teams=res["n_teams"],
        n_students_assigned=res["n_students_assigned"],
        n_students_unassigned=len(res["unassigned_students"]),
        runtime_seconds=res["runtime_seconds"]
    )
    db.add(gen_run)
    db.flush()

    # Save Teams & Members
    for t_data in res["teams"]:
        new_team = Team(
            project_id=project.id,
            name=t_data["name"],
            generation_method="baseline",
            run_id=gen_run.id,
            status="Proposed"
        )
        db.add(new_team)
        db.flush()

        for m_data in t_data["members"]:
            member = TeamMember(
                team_id=new_team.id,
                profile_id=m_data["profile_id"],
                assigned_role_id=m_data.get("assigned_role", {}).get("role_id"),
                matching_score=m_data["matching_score"],
                cluster_id=None,
                cluster_label="Rule-Based Deterministic"
            )
            db.add(member)
            db.flush()

            if m_data.get("assigned_role") and m_data["assigned_role"].get("role_id"):
                r_assign = RoleAssignment(
                    team_member_id=member.id,
                    role_id=m_data["assigned_role"]["role_id"],
                    fit_score=m_data["assigned_role"]["fit_score"],
                    rationale=m_data["assigned_role"]["rationale"]
                )
                db.add(r_assign)

    # Save Evaluation Result
    eval_record = EvaluationResult(
        run_id=gen_run.id,
        project_id=project.id,
        method="baseline",
        skill_coverage_ratio=eval_metrics["skill_coverage_ratio"],
        avg_skill_alignment=eval_metrics["avg_skill_alignment"],
        interest_alignment=eval_metrics["interest_alignment"],
        experience_alignment=eval_metrics["experience_alignment"],
        availability_compatibility=eval_metrics["availability_compatibility"],
        role_coverage=eval_metrics["role_coverage"],
        constraint_satisfaction_rate=eval_metrics["constraint_satisfaction_rate"],
        team_size_compliance=eval_metrics["team_size_compliance"],
        assignment_completeness=eval_metrics["assignment_completeness"],
        unassigned_count=eval_metrics["unassigned_count"],
        runtime_seconds=eval_metrics["runtime_seconds"]
    )
    db.add(eval_record)
    db.commit()

    flash(f"Baseline Teams successfully generated ({gen_run.n_teams} teams formed in {gen_run.runtime_seconds:.4f}s)!", "success")
    return redirect(url_for("generation.view_results", run_id=gen_run.id))

@generation_bp.route("/<int:project_id>/ml", methods=["POST"])
@login_required
@faculty_required
def run_ml_generation(project_id):
    db = get_db()
    project = ProjectService.get_project_by_id(project_id, session=db)
    if not project:
        flash("Project not found.", "warning")
        return redirect(url_for("faculty.projects_list"))

    n_clusters = int(request.form.get("n_clusters", 4))
    random_seed = int(request.form.get("random_seed", 42))

    eligible, ineligible = ProjectService.get_eligible_students(project.id, session=db)
    catalogs = StudentService.get_all_catalogs(session=db)

    # Execute ML-Guided Generation
    res = MLGuidedTeamEngine.generate_teams(
        eligible_students=eligible,
        project=project,
        catalogs=catalogs,
        n_clusters=n_clusters,
        random_seed=random_seed,
        db_session=db
    )

    if not res.get("success"):
        flash(f"AI/ML team recommendation failed: {res.get('error')}", "danger")
        return redirect(url_for("generation.project_generation_setup", project_id=project.id))

    # Recommend Roles for each team
    all_roles = db.query(Role).all()
    for t_data in res["teams"]:
        RoleRecommender.recommend_roles_for_team(
            team_members=t_data["members"],
            project=project,
            available_roles=all_roles
        )

    # Evaluate observable metrics
    eval_metrics = EvaluationService.evaluate_generation(
        teams_data=res["teams"],
        project=project,
        total_eligible_count=len(eligible),
        runtime_seconds=res["runtime_seconds"],
        method="ml"
    )

    # Persist in Database
    gen_run = TeamGenerationRun(
        project_id=project.id,
        method="ml",
        weights_json=json.dumps({"n_clusters": n_clusters, "random_seed": random_seed}),
        random_seed=random_seed,
        n_teams=res["n_teams"],
        n_students_assigned=res["n_students_assigned"],
        n_students_unassigned=len(res["unassigned_students"]),
        runtime_seconds=res["runtime_seconds"]
    )
    db.add(gen_run)
    db.flush()

    # Save Teams & Members
    for t_data in res["teams"]:
        new_team = Team(
            project_id=project.id,
            name=t_data["name"],
            generation_method="ml",
            run_id=gen_run.id,
            status="Proposed"
        )
        db.add(new_team)
        db.flush()

        for m_data in t_data["members"]:
            member = TeamMember(
                team_id=new_team.id,
                profile_id=m_data["profile_id"],
                assigned_role_id=m_data.get("assigned_role", {}).get("role_id"),
                matching_score=m_data["matching_score"],
                cluster_id=m_data.get("cluster_id"),
                cluster_label=m_data.get("cluster_label")
            )
            db.add(member)
            db.flush()

            if m_data.get("assigned_role") and m_data["assigned_role"].get("role_id"):
                r_assign = RoleAssignment(
                    team_member_id=member.id,
                    role_id=m_data["assigned_role"]["role_id"],
                    fit_score=m_data["assigned_role"]["fit_score"],
                    rationale=m_data.get("explanation") or m_data["assigned_role"]["rationale"]
                )
                db.add(r_assign)

    # Save Evaluation Result
    eval_record = EvaluationResult(
        run_id=gen_run.id,
        project_id=project.id,
        method="ml",
        skill_coverage_ratio=eval_metrics["skill_coverage_ratio"],
        avg_skill_alignment=eval_metrics["avg_skill_alignment"],
        interest_alignment=eval_metrics["interest_alignment"],
        experience_alignment=eval_metrics["experience_alignment"],
        availability_compatibility=eval_metrics["availability_compatibility"],
        role_coverage=eval_metrics["role_coverage"],
        constraint_satisfaction_rate=eval_metrics["constraint_satisfaction_rate"],
        team_size_compliance=eval_metrics["team_size_compliance"],
        assignment_completeness=eval_metrics["assignment_completeness"],
        unassigned_count=eval_metrics["unassigned_count"],
        runtime_seconds=eval_metrics["runtime_seconds"]
    )
    db.add(eval_record)
    db.commit()

    if res.get("warning"):
        flash(f"ML Note: {res['warning']}", "warning")
    flash(f"AI/ML K-Means Teams successfully formed ({gen_run.n_teams} teams in {gen_run.runtime_seconds:.4f}s)!", "success")
    return redirect(url_for("generation.view_results", run_id=gen_run.id))

@generation_bp.route("/results/<int:run_id>")
@login_required
@faculty_required
def view_results(run_id):
    user = get_current_user()
    db = get_db()
    run = db.query(TeamGenerationRun).filter_by(id=run_id).first()
    if not run:
        flash("Generation run not found.", "warning")
        return redirect(url_for("faculty.dashboard"))

    teams = db.query(Team).filter_by(run_id=run.id).all()
    eval_res = db.query(EvaluationResult).filter_by(run_id=run.id).first()

    template = "faculty/baseline_results.html" if run.method == "baseline" else "faculty/ml_results.html"
    return render_template(
        template,
        current_user=user,
        run=run,
        project=run.project,
        teams=teams,
        evaluation=eval_res
    )

@generation_bp.route("/review/<int:run_id>", methods=["GET", "POST"])
@login_required
@faculty_required
def review_and_edit_teams(run_id):
    user = get_current_user()
    db = get_db()
    run = db.query(TeamGenerationRun).filter_by(id=run_id).first()
    if not run:
        flash("Generation run not found.", "warning")
        return redirect(url_for("faculty.dashboard"))

    teams = db.query(Team).filter_by(run_id=run.id).all()
    roles = db.query(Role).all()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "finalize":
            # Approve and finalize teams
            for t in teams:
                t.status = "Finalized"
            run.project.status = "Formed"
            db.commit()
            flash("Teams have been officially approved and published to students!", "success")
            return redirect(url_for("faculty.dashboard"))

    return render_template(
        "faculty/team_review.html",
        current_user=user,
        run=run,
        project=run.project,
        teams=teams,
        roles=roles
    )
