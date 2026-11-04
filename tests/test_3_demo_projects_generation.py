"""
tests/test_3_demo_projects_generation.py
====================================================================
End-to-end verification of the 3 Demonstration Projects & AI Team Generation:
1. Project 1: AI-Powered Student Performance Prediction
2. Project 2: Smart Campus Management System
3. Project 3: AI-Powered Resume and Skill Gap Analyzer

Requirements Tested:
- Projects correctly configured with required skills and roles
- All 8 demo students eligible for each project (0 excluded)
- Baseline team generation forms 2 teams of 4 members (100% assignment, 0 duplicates)
- AI/ML (K-Means) team generation forms 2 teams of 4 members (100% assignment, 0 duplicates)
- Role assignment and skill coverage verification for both algorithms
- Generated teams persist and are reviewable in faculty dashboard
- Zero collision across projects (all 3 can be generated independently)
====================================================================
"""

import pytest
from database.db import get_db
from database.seed_data import seed_8_demo_students, seed_3_demo_projects
from services.project_service import ProjectService
from services.student_service import StudentService
from services.baseline_engine import RuleBasedTeamEngine
from services.role_recommender import RoleRecommender
from services.evaluation_service import EvaluationService
from ml.ml_team_engine import MLGuidedTeamEngine
from models.entities import Project, Team, TeamMember, TeamGenerationRun, Role

@pytest.fixture(scope="function")
def demo_3_env(db_session):
    """Sets up master catalogs, 8 demo students, and the 3 demonstration projects."""
    students, _ = seed_8_demo_students(session=db_session)
    projects = seed_3_demo_projects(session=db_session)
    catalogs = StudentService.get_all_catalogs(session=db_session)
    return {
        "session": db_session,
        "students": students,
        "projects": projects,
        "catalogs": catalogs
    }

def test_3_projects_configuration_and_requirements(demo_3_env):
    """Verifies that all 3 projects exist with correct domain, team size, skills, and roles."""
    db = demo_3_env["session"]
    projects = demo_3_env["projects"]
    
    assert len(projects) == 3, f"Expected 3 demo projects, got {len(projects)}"
    
    expected_projects = {
        "AI-Powered Student Performance Prediction": {
            "domain": "Machine Learning & Data Science",
            "skills": ["Python", "Machine Learning", "Pandas", "Scikit-learn", "SQL", "Data Analytics"],
            "roles": ["Data & ML Engineer", "Backend Developer", "QA / Testing Engineer", "Project Coordinator & Researcher"]
        },
        "Smart Campus Management System": {
            "domain": "Web Application Development",
            "skills": ["HTML/CSS", "JavaScript", "React", "Python", "SQL", "Backend Development"],
            "roles": ["Frontend Developer", "Backend Developer", "UI/UX Designer", "QA / Testing Engineer"]
        },
        "AI-Powered Resume and Skill Gap Analyzer": {
            "domain": "Machine Learning & Data Science",
            "skills": ["Python", "Machine Learning", "Scikit-learn", "HTML/CSS", "JavaScript", "SQL", "Data Science"],
            "roles": ["Data & ML Engineer", "Backend Developer", "Frontend Developer", "Project Coordinator & Researcher"]
        }
    }
    
    for p in projects:
        assert p.title in expected_projects, f"Unexpected project title: {p.title}"
        exp = expected_projects[p.title]
        assert p.domain == exp["domain"]
        assert p.desired_team_size == 4
        assert p.status == "Open"
        
        # Check required skills
        skill_names = {rs.skill.name for rs in p.required_skills}
        for s in exp["skills"]:
            assert s in skill_names, f"Skill '{s}' missing from project '{p.title}'"
            
        # Check required roles
        role_names = {rr.role.name for rr in p.required_roles}
        for r in exp["roles"]:
            assert r in role_names, f"Role '{r}' missing from project '{p.title}'"

def test_all_8_demo_students_eligible_for_all_3_projects(demo_3_env):
    """Verifies that all 8 demo students are 100% eligible (0 excluded) for each of the 3 projects."""
    db = demo_3_env["session"]
    projects = demo_3_env["projects"]
    
    for p in projects:
        eligible, ineligible = ProjectService.get_eligible_students(p.id, session=db)
        assert len(eligible) == 8, f"Project '{p.title}' expected 8 eligible students, got {len(eligible)}"
        assert len(ineligible) == 0, f"Project '{p.title}' had unexpected ineligible students: {ineligible}"
        
        eligible_ids = {s.student_id for s in eligible}
        for i in range(1, 9):
            assert f"DEMO-STU-00{i}" in eligible_ids

def _verify_project_team_generation(demo_3_env, project_title):
    """Helper that executes both Baseline and ML engines and verifies all constraints."""
    db = demo_3_env["session"]
    catalogs = demo_3_env["catalogs"]
    project = db.query(Project).filter_by(title=project_title).first()
    assert project is not None
    
    eligible, ineligible = ProjectService.get_eligible_students(project.id, session=db)
    assert len(eligible) == 8
    assert len(ineligible) == 0
    
    all_roles = db.query(Role).all()
    
    # 1. Rule-Based Baseline
    b_res = RuleBasedTeamEngine.generate_teams(
        eligible_students=eligible,
        project=project,
        weights=RuleBasedTeamEngine.DEFAULT_WEIGHTS,
        random_seed=42
    )
    
    assert b_res["success"] is True
    b_teams = b_res["teams"]
    assert len(b_teams) == 2, f"Baseline should produce 2 teams for '{project_title}'"
    
    b_student_ids = []
    for team in b_teams:
        assert len(team["members"]) == 4, "Each baseline team must have exactly 4 members"
        for m in team["members"]:
            b_student_ids.append(m["profile_id"])
            
        role_result = RoleRecommender.recommend_roles_for_team(
            team_members=team["members"],
            project=project,
            available_roles=all_roles
        )
        assert len(role_result["assignments"]) == 4
            
    # Zero duplicates
    assert len(b_student_ids) == 8
    assert len(set(b_student_ids)) == 8, "Duplicate students found in Baseline run!"
    
    # Baseline Evaluation
    b_eval = EvaluationService.evaluate_generation(
        teams_data=b_teams,
        project=project,
        total_eligible_count=len(eligible),
        runtime_seconds=b_res.get("runtime_seconds", 0.05),
        method="baseline"
    )
    assert b_eval["assignment_completeness"] == 1.0
    assert b_eval["unassigned_count"] == 0
    assert b_eval["team_size_compliance"] == 1.0
    assert b_eval["skill_coverage_ratio"] >= 0.70
    
    # 2. AI/ML Recommendation (K-Means)
    ml_res = MLGuidedTeamEngine.generate_teams(
        eligible_students=eligible,
        project=project,
        catalogs=catalogs,
        n_clusters=4,
        random_seed=42,
        db_session=db
    )
    
    assert ml_res["success"] is True
    ml_teams = ml_res["teams"]
    assert len(ml_teams) == 2, f"AI/ML should produce 2 teams for '{project_title}'"
    
    ml_student_ids = []
    for team in ml_teams:
        assert len(team["members"]) == 4, "Each AI/ML team must have exactly 4 members"
        for m in team["members"]:
            ml_student_ids.append(m["profile_id"])
            assert m["cluster_id"] is not None
            assert m["cluster_label"] is not None
            
        role_result = RoleRecommender.recommend_roles_for_team(
            team_members=team["members"],
            project=project,
            available_roles=all_roles
        )
        assert len(role_result["assignments"]) == 4
            
    # Zero duplicates
    assert len(ml_student_ids) == 8
    assert len(set(ml_student_ids)) == 8, "Duplicate students found in AI/ML run!"
    
    # AI/ML Evaluation
    ml_eval = EvaluationService.evaluate_generation(
        teams_data=ml_teams,
        project=project,
        total_eligible_count=len(eligible),
        runtime_seconds=ml_res.get("runtime_seconds", 0.05),
        method="ml"
    )
    assert ml_eval["assignment_completeness"] == 1.0
    assert ml_eval["unassigned_count"] == 0
    assert ml_eval["team_size_compliance"] == 1.0
    assert ml_eval["skill_coverage_ratio"] >= 0.70

def test_baseline_and_ml_team_generation_for_project_1(demo_3_env):
    """Verifies baseline and ML generation for Project 1: AI-Powered Student Performance Prediction."""
    _verify_project_team_generation(demo_3_env, "AI-Powered Student Performance Prediction")

def test_baseline_and_ml_team_generation_for_project_2(demo_3_env):
    """Verifies baseline and ML generation for Project 2: Smart Campus Management System."""
    _verify_project_team_generation(demo_3_env, "Smart Campus Management System")

def test_baseline_and_ml_team_generation_for_project_3(demo_3_env):
    """Verifies baseline and ML generation for Project 3: AI-Powered Resume and Skill Gap Analyzer."""
    _verify_project_team_generation(demo_3_env, "AI-Powered Resume and Skill Gap Analyzer")

def test_faculty_web_routes_for_all_3_projects(client, demo_3_env):
    """Verifies that faculty can access generation setup, run generation, and view comparison for all 3 projects."""
    projects = demo_3_env["projects"]
    
    # 1. Login as faculty
    client.post("/login", data={"email": "faculty@college.edu", "password": "Faculty@123"}, follow_redirects=True)
    
    for proj in projects:
        # Check generation setup view
        res = client.get(f"/generation/{proj.id}")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "Eligible Cohort for Matching: 8 Students" in html
        assert "producing <strong>2 teams</strong> of 4 members" in html
        
        # Post baseline generation
        b_res = client.post(
            f"/generation/{proj.id}/baseline",
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
        assert b_res.status_code == 200
        assert "Rule-Based Baseline" in b_res.get_data(as_text=True)
        
        # Post ML generation
        m_res = client.post(
            f"/generation/{proj.id}/ml",
            data={
                "n_clusters": "4",
                "random_seed": "42"
            },
            follow_redirects=True
        )
        assert m_res.status_code == 200
        assert "AI/ML Recommendation" in m_res.get_data(as_text=True)
        
        # Check Comparison view
        c_res = client.get(f"/comparison/{proj.id}")
        assert c_res.status_code == 200
