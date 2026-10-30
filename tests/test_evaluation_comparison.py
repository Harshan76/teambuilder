import pytest
from models.entities import Project, StudentProfile, Role
from services.baseline_engine import RuleBasedTeamEngine
from services.evaluation_service import EvaluationService
from services.export_service import ExportService
from services.role_recommender import RoleRecommender
from ml.ml_team_engine import MLGuidedTeamEngine
from services.student_service import StudentService

def test_evaluation_metric_calculations(db_session):
    project = db_session.query(Project).first()
    students = db_session.query(StudentProfile).all()
    roles = db_session.query(Role).all()

    # Generate baseline teams
    res = RuleBasedTeamEngine.generate_teams(students, project)
    for t in res["teams"]:
        RoleRecommender.recommend_roles_for_team(t["members"], project, roles)

    eval_res = EvaluationService.evaluate_generation(
        teams_data=res["teams"],
        project=project,
        total_eligible_count=len(students),
        runtime_seconds=res["runtime_seconds"],
        method="baseline"
    )

    # Check metrics are within valid ranges [0.0, 1.0]
    assert 0.0 <= eval_res["skill_coverage_ratio"] <= 1.0
    assert 0.0 <= eval_res["avg_skill_alignment"] <= 1.0
    assert 0.0 <= eval_res["interest_alignment"] <= 1.0
    assert 0.0 <= eval_res["experience_alignment"] <= 1.0
    assert 0.0 <= eval_res["availability_compatibility"] <= 1.0
    assert 0.0 <= eval_res["role_coverage"] <= 1.0
    assert 0.0 <= eval_res["constraint_satisfaction_rate"] <= 1.0
    assert 0.0 <= eval_res["team_size_compliance"] <= 1.0
    assert 0.0 <= eval_res["assignment_completeness"] <= 1.0
    assert eval_res["runtime_seconds"] >= 0.0

def test_side_by_side_comparison(db_session):
    project = db_session.query(Project).first()
    students = db_session.query(StudentProfile).all()
    roles = db_session.query(Role).all()
    catalogs = StudentService.get_all_catalogs(session=db_session)

    # 1. Baseline
    b_res = RuleBasedTeamEngine.generate_teams(students, project)
    for t in b_res["teams"]:
        RoleRecommender.recommend_roles_for_team(t["members"], project, roles)
    b_eval = EvaluationService.evaluate_generation(b_res["teams"], project, len(students), b_res["runtime_seconds"], "baseline")

    # 2. ML
    m_res = MLGuidedTeamEngine.generate_teams(students, project, catalogs)
    for t in m_res["teams"]:
        RoleRecommender.recommend_roles_for_team(t["members"], project, roles)
    m_eval = EvaluationService.evaluate_generation(m_res["teams"], project, len(students), m_res["runtime_seconds"], "ml")

    comparison = EvaluationService.compare_evaluations(b_eval, m_eval)
    assert "comparison_table" in comparison
    assert len(comparison["comparison_table"]) >= 9
    assert "commentary" in comparison

def test_csv_exports(db_session):
    project = db_session.query(Project).first()
    students = db_session.query(StudentProfile).all()

    # Generate baseline to export
    b_res = RuleBasedTeamEngine.generate_teams(students, project)
    comparison_data = {
        "comparison_table": [
            {
                "metric_name": "Skill Coverage Ratio",
                "description": "Coverage of project skills",
                "baseline_val": 0.85, "baseline_pct": 85.0,
                "ml_val": 0.90, "ml_pct": 90.0,
                "difference": 0.05,
                "verdict": "ML leads"
            }
        ],
        "commentary": ["Test note"]
    }

    comp_csv = ExportService.export_comparison_csv(comparison_data, project.title)
    assert "Metric Name" in comp_csv
    assert "Skill Coverage Ratio" in comp_csv
    assert "85.0%" in comp_csv
