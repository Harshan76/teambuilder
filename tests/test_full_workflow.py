import pytest
from models.entities import Project, Team, TeamMember, TeamGenerationRun

def test_full_college_demonstration_workflow(client, db_session):
    # 1. Log in as faculty
    login_res = client.post("/login", data={"email": "faculty@college.edu", "password": "Faculty@123"}, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Faculty &amp; Evaluation Dashboard" in login_res.data or b"Dashboard" in login_res.data

    # 2. Open the student directory
    students_res = client.get("/faculty/students")
    assert students_res.status_code == 200
    assert b"Student Profiles Directory" in students_res.data

    # 3. Inspect a student profile
    detail_res = client.get("/faculty/students/1")
    assert detail_res.status_code == 200
    assert b"Student Dossier" in detail_res.data or b"Alex Chen" in detail_res.data

    # 4. View projects list and select a project
    projects_res = client.get("/faculty/projects")
    assert projects_res.status_code == 200
    project = db_session.query(Project).filter_by(title="Intelligent HealthCare Analytics Portal").first()
    assert project is not None

    # 5. Open generation setup page
    setup_res = client.get(f"/generation/{project.id}")
    assert setup_res.status_code == 200
    assert b"Team Generation Control Center" in setup_res.data

    # 6. Generate teams using the rule-based baseline
    baseline_gen = client.post(
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
    assert baseline_gen.status_code == 200
    assert b"Rule-Based Baseline Results" in baseline_gen.data

    # 7. Generate teams using the ML-based approach on the same eligible cohort
    ml_gen = client.post(
        f"/generation/{project.id}/ml",
        data={
            "n_clusters": "4",
            "random_seed": "42"
        },
        follow_redirects=True
    )
    assert ml_gen.status_code == 200
    assert b"AI/ML Recommendation Results" in ml_gen.data
    assert b"Discovered Archetype" in ml_gen.data or b"Recommendation Rationale" in ml_gen.data

    # 8. Open the comparison dashboard
    comp_res = client.get(f"/comparison/{project.id}")
    assert comp_res.status_code == 200
    assert b"Algorithmic Comparison &amp; Evaluation Module" in comp_res.data or b"Comparison" in comp_res.data
    assert b"Multi-Dimensional Assignment Performance Chart" in comp_res.data

    # 9. Review and edit teams
    latest_run = db_session.query(TeamGenerationRun).filter_by(project_id=project.id).order_by(TeamGenerationRun.created_at.desc()).first()
    review_res = client.get(f"/generation/review/{latest_run.id}")
    assert review_res.status_code == 200
    assert b"Team Review &amp; Manual Override" in review_res.data or b"Team Review" in review_res.data

    # 10. Approve and finalize teams
    finalize_res = client.post(f"/generation/review/{latest_run.id}", data={"action": "finalize"}, follow_redirects=True)
    assert finalize_res.status_code == 200
    assert b"approved and published to students" in finalize_res.data

    # Verify teams status updated to Finalized in database
    finalized_teams = db_session.query(Team).filter_by(run_id=latest_run.id, status="Finalized").all()
    assert len(finalized_teams) > 0

    # 11. Download CSV exports
    csv_teams = client.get(f"/reports/{project.id}/export/teams")
    assert csv_teams.status_code == 200
    assert "text/csv" in csv_teams.content_type
    assert b"Team Name" in csv_teams.data

    csv_comp = client.get(f"/reports/{project.id}/export/comparison")
    assert csv_comp.status_code == 200
    assert "text/csv" in csv_comp.content_type
    assert b"Metric Name" in csv_comp.data
