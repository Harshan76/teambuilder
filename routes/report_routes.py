from flask import Blueprint, render_template, request, Response, redirect, url_for, flash
from database.db import get_db
from models.entities import Project, Team, TeamGenerationRun, EvaluationResult
from services.auth_service import login_required, faculty_required, get_current_user
from services.project_service import ProjectService
from services.export_service import ExportService
from services.evaluation_service import EvaluationService

report_bp = Blueprint("report", __name__, url_prefix="/reports")

@report_bp.route("/<int:project_id>")
@login_required
@faculty_required
def project_reports(project_id):
    user = get_current_user()
    db = get_db()
    project = ProjectService.get_project_by_id(project_id, session=db)
    if not project:
        flash("Project not found.", "warning")
        return redirect(url_for("faculty.projects_list"))

    runs = db.query(TeamGenerationRun).filter_by(project_id=project.id).order_by(TeamGenerationRun.created_at.desc()).all()
    teams = db.query(Team).filter_by(project_id=project.id).all()

    return render_template(
        "faculty/reports.html",
        current_user=user,
        project=project,
        runs=runs,
        teams=teams
    )

@report_bp.route("/<int:project_id>/export/teams")
@login_required
@faculty_required
def export_teams(project_id):
    db = get_db()
    project = ProjectService.get_project_by_id(project_id, session=db)
    if not project:
        return "Project not found", 404

    # Export finalized teams if available, else latest generated teams
    teams = db.query(Team).filter_by(project_id=project.id, status="Finalized").all()
    if not teams:
        teams = db.query(Team).filter_by(project_id=project.id).all()

    csv_data = ExportService.export_teams_csv(teams, project)
    filename = f"teams_export_{project.id}_{project.title[:15].replace(' ', '_')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@report_bp.route("/<int:project_id>/export/comparison")
@login_required
@faculty_required
def export_comparison(project_id):
    db = get_db()
    project = ProjectService.get_project_by_id(project_id, session=db)
    if not project:
        return "Project not found", 404

    baseline_run = db.query(TeamGenerationRun).filter_by(
        project_id=project.id, method="baseline"
    ).order_by(TeamGenerationRun.created_at.desc()).first()

    ml_run = db.query(TeamGenerationRun).filter_by(
        project_id=project.id, method="ml"
    ).order_by(TeamGenerationRun.created_at.desc()).first()

    if not baseline_run or not ml_run:
        flash("Both Baseline and ML runs must be generated before exporting comparison report.", "warning")
        return redirect(url_for("report.project_reports", project_id=project.id))

    b_rec = db.query(EvaluationResult).filter_by(run_id=baseline_run.id).first()
    m_rec = db.query(EvaluationResult).filter_by(run_id=ml_run.id).first()

    baseline_eval = {
        "skill_coverage_ratio": b_rec.skill_coverage_ratio,
        "avg_skill_alignment": b_rec.avg_skill_alignment,
        "interest_alignment": b_rec.interest_alignment,
        "experience_alignment": b_rec.experience_alignment,
        "availability_compatibility": b_rec.availability_compatibility,
        "role_coverage": b_rec.role_coverage,
        "constraint_satisfaction_rate": b_rec.constraint_satisfaction_rate,
        "team_size_compliance": b_rec.team_size_compliance,
        "assignment_completeness": b_rec.assignment_completeness,
        "runtime_seconds": b_rec.runtime_seconds
    }
    ml_eval = {
        "skill_coverage_ratio": m_rec.skill_coverage_ratio,
        "avg_skill_alignment": m_rec.avg_skill_alignment,
        "interest_alignment": m_rec.interest_alignment,
        "experience_alignment": m_rec.experience_alignment,
        "availability_compatibility": m_rec.availability_compatibility,
        "role_coverage": m_rec.role_coverage,
        "constraint_satisfaction_rate": m_rec.constraint_satisfaction_rate,
        "team_size_compliance": m_rec.team_size_compliance,
        "assignment_completeness": m_rec.assignment_completeness,
        "runtime_seconds": m_rec.runtime_seconds
    }

    comparison_data = EvaluationService.compare_evaluations(baseline_eval, ml_eval)
    csv_data = ExportService.export_comparison_csv(comparison_data, project.title)
    filename = f"comparison_report_{project.id}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
