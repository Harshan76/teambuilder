import pytest
from models.entities import StudentProfile, Project
from services.student_service import StudentService
from services.project_service import ProjectService

def test_profile_completion_check(db_session):
    # Complete student profile
    student = db_session.query(StudentProfile).first()
    is_complete, missing, pct = StudentService.check_profile_completion(student)
    assert is_complete is True
    assert len(missing) == 0
    assert pct == 100

    # Incomplete student profile (missing skills)
    empty_student = StudentProfile(
        user_id=student.user_id,
        student_id="STU-EMPTY",
        department="Computer Science",
        is_profile_complete=False
    )
    is_comp, miss, empty_pct = StudentService.check_profile_completion(empty_student)
    assert is_comp is False
    assert len(miss) > 0
    assert empty_pct < 100

def test_project_requirements_validation(db_session):
    faculty = db_session.query(StudentProfile).first().user

    # Valid project creation
    valid_data = {
        "title": "Autonomous Drone Fleet",
        "domain": "Internet of Things (IoT)",
        "desired_team_size": 4,
        "min_team_size": 3,
        "max_team_size": 5,
        "required_skills": [],
        "required_roles": []
    }
    proj = ProjectService.create_project(valid_data, creator_id=faculty.id, session=db_session)
    assert proj.id is not None
    assert proj.desired_team_size == 4

    # Invalid project: desired_team_size < 2
    with pytest.raises(ValueError, match="Desired team size must be at least 2"):
        ProjectService.create_project({**valid_data, "desired_team_size": 1}, creator_id=faculty.id, session=db_session)

    # Invalid project: min > max
    with pytest.raises(ValueError, match="Team sizes must satisfy"):
        ProjectService.create_project({**valid_data, "min_team_size": 5, "max_team_size": 3}, creator_id=faculty.id, session=db_session)

def test_student_eligibility_enforcement(db_session):
    project = db_session.query(Project).first()
    eligible, ineligible = ProjectService.get_eligible_students(project.id, session=db_session)
    
    # In seeded dataset, all 24 synthetic students have complete profiles and should be eligible
    assert len(eligible) >= 20
    assert isinstance(eligible[0], StudentProfile)
