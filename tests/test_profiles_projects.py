import pytest
from models.entities import StudentProfile, Project, User
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
    
    # In seeded dataset, synthetic students have complete profiles and are eligible
    assert len(eligible) >= 20
    assert isinstance(eligible[0], StudentProfile)

def test_eligibility_with_incomplete_optional_info_and_exclusion_reasons(db_session):
    project = db_session.query(Project).first()
    
    # 1. Create a student with skills and availability, but NO optional interests or preferred roles
    user = User(email="partial.profile@college.edu", full_name="Partial Profile Student", role="student")
    user.set_password("Student@123")
    db_session.add(user)
    db_session.flush()
    
    profile = StudentProfile(
        user_id=user.id,
        student_id="DEMO-PARTIAL-001",
        department="Computer Science",
        experience_level="Intermediate",
        experience_years=2.0
    )
    db_session.add(profile)
    db_session.flush()
    
    # Add 1 skill and 1 availability slot
    from models.entities import Skill, AvailabilitySlot, StudentSkill, StudentAvailability
    sk = db_session.query(Skill).first()
    slot = db_session.query(AvailabilitySlot).first()
    db_session.add(StudentSkill(profile_id=profile.id, skill_id=sk.id, proficiency=3))
    db_session.add(StudentAvailability(profile_id=profile.id, slot_id=slot.id))
    db_session.commit()
    
    # Must be ELIGIBLE because mandatory matching fields exist (even though optional interests/roles are empty)
    eligible, ineligible = ProjectService.get_eligible_students(project.id, session=db_session)
    eligible_ids = [p.id for p in eligible]
    assert profile.id in eligible_ids
    
    # 2. Create student with 0 technical skills
    user_no_sk = User(email="noskill.student@college.edu", full_name="No Skill Student", role="student")
    user_no_sk.set_password("Student@123")
    db_session.add(user_no_sk)
    db_session.flush()
    profile_no_sk = StudentProfile(
        user_id=user_no_sk.id,
        student_id="DEMO-NOSK-001",
        department="Computer Science",
        experience_level="Intermediate"
    )
    db_session.add(profile_no_sk)
    db_session.flush()
    db_session.add(StudentAvailability(profile_id=profile_no_sk.id, slot_id=slot.id))
    db_session.commit()
    
    eligible2, ineligible2 = ProjectService.get_eligible_students(project.id, session=db_session)
    ineligible_dict = {i["profile_id"]: i["reason"] for i in ineligible2}
    assert profile_no_sk.id in ineligible_dict
    assert "No technical skills recorded" in ineligible_dict[profile_no_sk.id]

def test_skill_selection_and_persistence(client, db_session):
    from models.entities import Skill, StudentSkill
    # 1. Login as student
    client.post("/login", data={"email": "student1@college.edu", "password": "Student@123"}, follow_redirects=True)
    
    # 2. Query available skills
    skills = db_session.query(Skill).limit(3).all()
    assert len(skills) >= 2
    
    # 3. Post profile update with skills
    form_data = {
        "full_name": "Alex Chen Updated",
        "student_id": "DEMO-2026-001",
        "department": "Computer Science",
        "experience_level": "Advanced",
        "experience_years": "3.5",
        "previous_projects_summary": "Extensive microservice deployments.",
        "selected_skill_id": [str(skills[0].id), str(skills[1].id)],
        "selected_skill_proficiency": ["4", "5"],
        "role_rank_1": "1"
    }
    res = client.post("/student/profile", data=form_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Profile and technical skills updated successfully" in res.data or b"Profile updated successfully" in res.data
    
    # 4. Verify skills persisted in database
    student_user = db_session.query(User).filter_by(email="student1@college.edu").first()
    student_skills = {ss.skill_id: ss.proficiency for ss in student_user.profile.skills}
    assert student_skills[skills[0].id] == 4
    assert student_skills[skills[1].id] == 5

def test_student_skills_api_endpoints(client, db_session):
    from models.entities import Skill
    client.post("/login", data={"email": "student1@college.edu", "password": "Student@123"}, follow_redirects=True)
    
    # 1. GET /api/student/skills
    res = client.get("/api/student/skills")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["catalog"]) > 0
    
    # 2. POST /api/student/skills (Add or update skill)
    target_skill = db_session.query(Skill).first()
    save_res = client.post("/api/student/skills", json={"skill_id": target_skill.id, "proficiency": 5})
    assert save_res.status_code == 200
    save_data = save_res.get_json()
    assert save_data["success"] is True
    assert save_data["skill"]["proficiency"] == 5
    
    # 3. DELETE /api/student/skills/<id>
    del_res = client.delete(f"/api/student/skills/{target_skill.id}")
    assert del_res.status_code == 200
    del_data = del_res.get_json()
    assert del_data["success"] is True

def test_health_check_endpoint(client):
    res1 = client.get("/health")
    assert res1.status_code == 200
    data1 = res1.get_json()
    assert data1["status"] == "healthy"
    assert data1["database"] == "connected"

    res2 = client.get("/api/health")
    assert res2.status_code == 200
    assert res2.get_json()["status"] == "healthy"
