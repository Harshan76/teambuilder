import pytest
from models.entities import StudentProfile, Project, Role
from services.role_recommender import RoleRecommender

def test_role_fitness_and_rationale(db_session):
    student = db_session.query(StudentProfile).first()
    role = db_session.query(Role).filter_by(name="Backend Developer").first()

    score, rationale = RoleRecommender.calculate_role_fitness(student, role)
    assert 0 <= score <= 100
    assert len(rationale) > 0
    assert isinstance(rationale, str)

def test_team_role_recommendation_and_assignment(db_session):
    project = db_session.query(Project).first()
    students = db_session.query(StudentProfile).limit(4).all()
    roles = db_session.query(Role).all()

    mock_team_members = [{"profile": s, "profile_id": s.id} for s in students]

    res = RoleRecommender.recommend_roles_for_team(
        team_members=mock_team_members,
        project=project,
        available_roles=roles
    )

    assert "assignments" in res
    assert len(res["assignments"]) == 4
    for m in mock_team_members:
        assert "assigned_role" in m
        assert m["assigned_role"]["role_id"] is not None
        assert len(m["assigned_role"]["rationale"]) > 0
