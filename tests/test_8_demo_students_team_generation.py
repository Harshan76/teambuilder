"""
tests/test_8_demo_students_team_generation.py
====================================================================
End-to-end verification of the 8 Demo Student Profiles and Team Generation:
1. Validates 8 unique demo student profiles and mandatory fields.
2. Validates team-generation eligibility criteria compliance (8 eligible, 0 excluded).
3. Executes Rule-Based Baseline formation: 8 students -> 2 teams of 4 members.
4. Executes AI/ML Recommendation (K-Means): 8 students -> 2 teams of 4 members.
5. Verifies zero duplicate assignments across teams within each run.
6. Verifies complementary skill and role coverage across generated teams.
7. Tests Flask web endpoints for baseline, ML, and comparison dashboards.
====================================================================
"""

import pytest
from database.db import db_manager, get_db
from database.seed_data import seed_8_demo_students, ensure_master_catalogs
from services.project_service import ProjectService
from services.student_service import StudentService
from services.baseline_engine import RuleBasedTeamEngine
from services.role_recommender import RoleRecommender
from services.evaluation_service import EvaluationService
from ml.ml_team_engine import MLGuidedTeamEngine
from models.entities import User, StudentProfile, Project, Role, Team, TeamMember, TeamGenerationRun

@pytest.fixture(scope="function")
def demo_env(db_session):
    """Sets up fresh master catalogs, 8 demo students, and showcase project."""
    students, project = seed_8_demo_students(session=db_session)
    catalogs = StudentService.get_all_catalogs(session=db_session)
    return {
        "session": db_session,
        "students": students,
        "project": project,
        "catalogs": catalogs
    }

def test_8_demo_students_attributes_and_profile_completeness(demo_env):
    """Verifies that all 8 demo students have unique credentials and 100% complete profiles."""
    db = demo_env["session"]
    students = demo_env["students"]
    
    assert len(students) == 8, "Expected exactly 8 demo student profiles."

    emails = set()
    student_ids = set()

    for s in students:
        user = s.user
        assert user is not None
        assert user.role == "student"
        assert "[DEMO]" in user.full_name
        assert user.email.startswith("demo.student")
        assert s.student_id.startswith("DEMO-STU-")

        # Uniqueness
        assert user.email not in emails
        assert s.student_id not in student_ids
        emails.add(user.email)
        student_ids.add(s.student_id)

        # Profile fields
        assert s.department is not None and len(s.department) > 0
        assert s.experience_level in ["Intermediate", "Advanced"]
        assert s.experience_years >= 1.5
        assert s.previous_projects_summary is not None and len(s.previous_projects_summary) > 20

        # Relational requirements
        assert len(s.skills) >= 4, f"Student {s.student_id} must have at least 4 skills."
        for ss in s.skills:
            assert 1 <= ss.proficiency <= 5

        assert len(s.interests) >= 2, f"Student {s.student_id} must have at least 2 interests."
        assert len(s.availability) >= 2, f"Student {s.student_id} must have at least 2 availability slots."
        assert len(s.preferred_roles) >= 2, f"Student {s.student_id} must have at least 2 preferred roles."

        # Completeness check
        is_complete, missing, pct = StudentService.check_profile_completion(s)
        assert is_complete is True
        assert len(missing) == 0
        assert pct == 100
        assert s.is_profile_complete is True

        # Password hash verification
        assert user.check_password("Student@123") is True

def test_8_demo_students_eligibility(demo_env):
    """Verifies that all 8 demo students satisfy the actual project eligibility rules."""
    db = demo_env["session"]
    project = demo_env["project"]

    eligible, ineligible = ProjectService.get_eligible_students(project.id, session=db)

    assert len(eligible) == 8, f"Expected 8 eligible students, got {len(eligible)}."
    assert len(ineligible) == 0, f"Expected 0 ineligible students, got {ineligible}."

    eligible_ids = {s.student_id for s in eligible}
    for i in range(1, 9):
        expected_id = f"DEMO-STU-00{i}"
        assert expected_id in eligible_ids

def test_rule_based_baseline_team_generation(demo_env):
    """Verifies Rule-Based Baseline generates 2 teams of 4 with zero duplicate assignments."""
    db = demo_env["session"]
    project = demo_env["project"]
    catalogs = demo_env["catalogs"]
    eligible_students = demo_env["students"]

    assert project.desired_team_size == 4

    result = RuleBasedTeamEngine.generate_teams(
        eligible_students=eligible_students,
        project=project,
        weights=RuleBasedTeamEngine.DEFAULT_WEIGHTS,
        random_seed=42
    )

    assert result["success"] is True
    teams = result["teams"]
    assert len(teams) == 2, f"Expected 2 teams for 8 students with team size 4, got {len(teams)}."

    all_assigned_ids = []
    for idx, team in enumerate(teams, start=1):
        members = team["members"]
        assert len(members) == 4, f"Team {idx} should have exactly 4 members, got {len(members)}."
        team_member_ids = [m["profile_id"] for m in members]
        all_assigned_ids.extend(team_member_ids)

    # Check zero overlap / no duplicate assignments
    assert len(all_assigned_ids) == 8
    assert len(set(all_assigned_ids)) == 8, "No student should appear in multiple teams."

    # Check Role Recommendations
    all_roles = db.query(Role).all()
    for team in teams:
        role_result = RoleRecommender.recommend_roles_for_team(
            team_members=team["members"],
            project=project,
            available_roles=all_roles
        )
        assignments = role_result["assignments"]
        assert len(assignments) == 4
        # Verify recommended roles cover distinct project needs
        role_ids = [ar["role_id"] for ar in assignments.values()]
        assert len(set(role_ids)) >= 3, "Team should have diverse complementary role coverage."

    # Check Evaluation Metrics
    eval_metrics = EvaluationService.evaluate_generation(
        teams_data=teams,
        project=project,
        total_eligible_count=len(eligible_students),
        runtime_seconds=result.get("runtime_seconds", 0.05),
        method="baseline"
    )
    assert eval_metrics["assignment_completeness"] == 1.0
    assert eval_metrics["unassigned_count"] == 0
    assert eval_metrics["skill_coverage_ratio"] > 0.60
    assert eval_metrics["team_size_compliance"] == 1.0

def test_ml_guided_team_generation(demo_env):
    """Verifies AI/ML K-Means clustering generates 2 balanced teams of 4 from the 8 demo students."""
    db = demo_env["session"]
    project = demo_env["project"]
    catalogs = demo_env["catalogs"]
    eligible_students = demo_env["students"]

    result = MLGuidedTeamEngine.generate_teams(
        eligible_students=eligible_students,
        project=project,
        catalogs=catalogs,
        n_clusters=4,
        random_seed=42,
        db_session=db
    )

    assert result["success"] is True
    teams = result["teams"]
    assert len(teams) == 2, f"Expected 2 teams for 8 students with team size 4, got {len(teams)}."

    all_assigned_ids = []
    for idx, team in enumerate(teams, start=1):
        members = team["members"]
        assert len(members) == 4, f"Team {idx} should have exactly 4 members, got {len(members)}."
        team_member_ids = [m["profile_id"] for m in members]
        all_assigned_ids.extend(team_member_ids)

    # Check zero overlap / no duplicate assignments
    assert len(all_assigned_ids) == 8
    assert len(set(all_assigned_ids)) == 8, "No student should appear in multiple teams."

    # Verify cluster archetypes were assigned to all members
    for team in teams:
        for m in team["members"]:
            assert m["cluster_id"] is not None
            assert m["cluster_label"] is not None

    # Check Evaluation Metrics
    eval_metrics = EvaluationService.evaluate_generation(
        teams_data=teams,
        project=project,
        total_eligible_count=len(eligible_students),
        runtime_seconds=result.get("runtime_seconds", 0.05),
        method="ml"
    )
    assert eval_metrics["assignment_completeness"] == 1.0
    assert eval_metrics["unassigned_count"] == 0
    assert eval_metrics["skill_coverage_ratio"] > 0.60
    assert eval_metrics["team_size_compliance"] == 1.0

def test_both_approaches_use_same_pool_and_yield_equal_team_count(demo_env):
    """Verifies side-by-side consistency: Baseline and ML operate on the exact same pool."""
    db = demo_env["session"]
    project = demo_env["project"]
    catalogs = demo_env["catalogs"]
    eligible_students = demo_env["students"]

    # 1. Run Baseline
    base_res = RuleBasedTeamEngine.generate_teams(
        eligible_students=eligible_students,
        project=project,
        weights=RuleBasedTeamEngine.DEFAULT_WEIGHTS,
        random_seed=42
    )
    # 2. Run ML
    ml_res = MLGuidedTeamEngine.generate_teams(
        eligible_students=eligible_students,
        project=project,
        catalogs=catalogs,
        n_clusters=4,
        random_seed=42,
        db_session=db
    )

    assert len(base_res["teams"]) == 2
    assert len(ml_res["teams"]) == 2

    base_students = {m["profile_id"] for t in base_res["teams"] for m in t["members"]}
    ml_students = {m["profile_id"] for t in ml_res["teams"] for m in t["members"]}

    assert base_students == ml_students, "Both algorithms must assign the exact same set of 8 students."
    assert len(base_students) == 8

def test_web_routes_team_generation_and_comparison(client, demo_env):
    """Verifies the complete faculty web workflow for generation and comparison dashboards."""
    project = demo_env["project"]

    # 1. Login as faculty
    client.post("/login", data={"email": "faculty@college.edu", "password": "Faculty@123"}, follow_redirects=True)

    # 2. Inspect Generation Setup View
    res = client.get(f"/generation/{project.id}")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Eligible Cohort for Matching: 8 Students" in html
    assert "producing <strong>2 teams</strong> of 4 members" in html

    # 3. Post Rule-Based Baseline Generation
    res_base = client.post(
        f"/generation/{project.id}/baseline",
        data={
            "weight_skill": "0.40",
            "weight_interest": "0.20",
            "weight_experience": "0.15",
            "weight_availability": "0.15",
            "weight_role": "0.10",
            "random_seed": "42"
        },
        follow_redirects=True
    )
    assert res_base.status_code == 200
    base_html = res_base.get_data(as_text=True)
    assert "Rule-Based Baseline" in base_html

    # 4. Post ML Recommendation Generation
    res_ml = client.post(
        f"/generation/{project.id}/ml",
        data={
            "n_clusters": "4",
            "random_seed": "42"
        },
        follow_redirects=True
    )
    assert res_ml.status_code == 200
    ml_html = res_ml.get_data(as_text=True)
    assert "AI/ML Recommendation" in ml_html or "Scikit-Learn K-Means" in ml_html

    # 5. Check Comparison Dashboard
    comp_res = client.get(f"/comparison/{project.id}")
    assert comp_res.status_code == 200
    comp_html = comp_res.get_data(as_text=True)
    assert "Side-by-Side Algorithm Comparison" in comp_html or "Comparison" in comp_html
    assert "Baseline" in comp_html
    assert "Machine Learning" in comp_html or "AI/ML" in comp_html
