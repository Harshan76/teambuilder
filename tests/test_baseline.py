import pytest
from models.entities import StudentProfile, Project
from services.baseline_engine import RuleBasedTeamEngine

def test_weights_validation():
    # Valid weights that normalize
    w = RuleBasedTeamEngine.validate_weights({
        "technical_skill": 0.4,
        "interest_domain": 0.2,
        "experience": 0.2,
        "availability": 0.1,
        "preferred_role": 0.1
    })
    assert sum(w.values()) == pytest.approx(1.0, 0.01)

    # Negative weight raises ValueError
    with pytest.raises(ValueError, match="cannot be negative"):
        RuleBasedTeamEngine.validate_weights({"technical_skill": -0.1})

    # Zero sum raises ValueError
    with pytest.raises(ValueError, match="greater than zero"):
        RuleBasedTeamEngine.validate_weights({
            "technical_skill": 0, "interest_domain": 0, "experience": 0,
            "availability": 0, "preferred_role": 0
        })

def test_baseline_score_calculation(db_session):
    project = db_session.query(Project).filter_by(title="Intelligent HealthCare Analytics Portal").first()
    student = db_session.query(StudentProfile).first()

    weights = RuleBasedTeamEngine.DEFAULT_WEIGHTS
    score_res = RuleBasedTeamEngine.calculate_student_score(student, project, weights)

    assert "total_score" in score_res
    assert 0 <= score_res["total_score"] <= 100
    assert 0 <= score_res["skill_score"] <= 100
    assert 0 <= score_res["interest_score"] <= 100
    assert 0 <= score_res["experience_score"] <= 100
    assert 0 <= score_res["availability_score"] <= 100
    assert 0 <= score_res["role_score"] <= 100

def test_baseline_team_formation_constraints(db_session):
    project = db_session.query(Project).filter_by(title="Intelligent HealthCare Analytics Portal").first()
    students = db_session.query(StudentProfile).all()

    res = RuleBasedTeamEngine.generate_teams(
        eligible_students=students,
        project=project,
        random_seed=42
    )

    assert res["success"] is True
    assert res["n_teams"] > 0

    assigned_students = set()
    for t in res["teams"]:
        # Verify team size bounds
        assert len(t["members"]) == project.desired_team_size
        for m in t["members"]:
            # Verify no duplicate student assignment
            assert m["profile_id"] not in assigned_students
            assigned_students.add(m["profile_id"])

    # Total assigned + unassigned equals cohort total
    total_accounted = len(assigned_students) + len(res["unassigned_students"])
    assert total_accounted == len(students)

def test_baseline_insufficient_students_edge_case(db_session):
    project = db_session.query(Project).first()
    single_student = [db_session.query(StudentProfile).first()]

    res = RuleBasedTeamEngine.generate_teams(
        eligible_students=single_student,
        project=project
    )
    assert res["success"] is False
    assert "Insufficient eligible students" in res["error"]
