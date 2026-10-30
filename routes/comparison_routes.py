import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db
from models.entities import Project, TeamGenerationRun, EvaluationResult
from services.auth_service import login_required, faculty_required, get_current_user
from services.project_service import ProjectService
from services.evaluation_service import EvaluationService

comparison_bp = Blueprint("comparison", __name__, url_prefix="/comparison")

@comparison_bp.route("/<int:project_id>")
@login_required
@faculty_required
def compare_project_runs(project_id):
    user = get_current_user()
    db = get_db()
    project = ProjectService.get_project_by_id(project_id, session=db)
    if not project:
        flash("Project not found.", "warning")
        return redirect(url_for("faculty.projects_list"))

    # Fetch latest baseline run and latest ml run for this project
    baseline_run = db.query(TeamGenerationRun).filter_by(
        project_id=project.id, method="baseline"
    ).order_by(TeamGenerationRun.created_at.desc()).first()

    ml_run = db.query(TeamGenerationRun).filter_by(
        project_id=project.id, method="ml"
    ).order_by(TeamGenerationRun.created_at.desc()).first()

    baseline_eval = None
    ml_eval = None
    comparison_data = None
    chart_data_json = "{}"

    if baseline_run:
        b_rec = db.query(EvaluationResult).filter_by(run_id=baseline_run.id).first()
        if b_rec:
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
                "runtime_seconds": b_rec.runtime_seconds,
                "n_teams": baseline_run.n_teams,
                "n_students_assigned": baseline_run.n_students_assigned,
                "unassigned_count": baseline_run.n_students_unassigned
            }

    if ml_run:
        m_rec = db.query(EvaluationResult).filter_by(run_id=ml_run.id).first()
        if m_rec:
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
                "runtime_seconds": m_rec.runtime_seconds,
                "n_teams": ml_run.n_teams,
                "n_students_assigned": ml_run.n_students_assigned,
                "unassigned_count": ml_run.n_students_unassigned
            }

    if baseline_eval and ml_eval:
        comparison_data = EvaluationService.compare_evaluations(baseline_eval, ml_eval)

        # Prepare Chart.js payload
        chart_labels = [row["metric_name"] for row in comparison_data["comparison_table"]]
        baseline_vals = [row["baseline_pct"] for row in comparison_data["comparison_table"]]
        ml_vals = [row["ml_pct"] for row in comparison_data["comparison_table"]]

        chart_payload = {
            "labels": chart_labels,
            "datasets": [
                {
                    "label": "Rule-Based Baseline (%)",
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 2,
                    "data": baseline_vals
                },
                {
                    "label": "AI/ML Guided Approach (%)",
                    "backgroundColor": "rgba(153, 102, 255, 0.5)",
                    "borderColor": "rgba(153, 102, 255, 1)",
                    "borderWidth": 2,
                    "data": ml_vals
                }
            ]
        }
        chart_data_json = json.dumps(chart_payload)

    return render_template(
        "faculty/comparison.html",
        current_user=user,
        project=project,
        baseline_run=baseline_run,
        ml_run=ml_run,
        baseline_eval=baseline_eval,
        ml_eval=ml_eval,
        comparison_data=comparison_data,
        chart_data_json=chart_data_json
    )
