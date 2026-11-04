import pytest
from database.db import db_manager, Base
from database.seed_data import ensure_master_catalogs
from services.student_service import StudentService
from models.entities import Skill, Interest, AvailabilitySlot, Role, User, StudentProfile
from models.constants import DEPARTMENTS, DOMAINS

def test_ensure_master_catalogs_is_idempotent_and_creates_no_users(db_session):
    """Verifies that ensure_master_catalogs populates all reference tables without creating users."""
    initial_user_count = db_session.query(User).count()
    
    # Run once
    stats1 = ensure_master_catalogs(session=db_session)
    assert stats1["skills_count"] == 27
    assert stats1["interests_count"] == 7
    assert stats1["slots_count"] == 6
    assert stats1["roles_count"] == 6

    # Verify no fake user was created
    assert db_session.query(User).count() == initial_user_count

    # Run second time (idempotency check)
    stats2 = ensure_master_catalogs(session=db_session)
    assert stats2["skills_count"] == 27
    assert db_session.query(Skill).count() == 27
    assert db_session.query(Interest).count() == 7
    assert db_session.query(AvailabilitySlot).count() == 6
    assert db_session.query(Role).count() == 6

def test_student_service_get_all_catalogs_self_healing():
    """Verifies that get_all_catalogs self-heals when queried against empty database."""
    # Create isolated fresh memory engine
    db_manager.init_db(uri_override="sqlite:///:memory:")
    Base.metadata.drop_all(db_manager.engine)
    Base.metadata.create_all(db_manager.engine)
    session = db_manager.get_session()

    # Verify tables start completely empty
    assert session.query(Skill).count() == 0
    assert session.query(Interest).count() == 0

    # Call get_all_catalogs: should auto-heal and return all reference items
    catalogs = StudentService.get_all_catalogs(session=session)
    assert len(catalogs["skills"]) == 27
    assert len(catalogs["interests"]) == 7
    assert len(catalogs["slots"]) == 6
    assert len(catalogs["roles"]) == 6
    session.close()

def test_api_catalogs_and_skills_endpoints(client, db_session):
    """Verifies that API endpoints return structured catalogs for frontend components."""
    # Login as student with valid credentials
    login_res = client.post("/login", data={"email": "student1@college.edu", "password": "Student@123"}, follow_redirects=True)
    assert login_res.status_code == 200

    # 1. Test /api/student/skills
    res = client.get("/api/student/skills")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["catalog"]) == 27
    assert any(s["name"] == "Python" for s in data["catalog"])

    # 2. Test /api/catalogs
    res2 = client.get("/api/catalogs")
    assert res2.status_code == 200
    cat_data = res2.get_json()
    assert cat_data["success"] is True
    assert len(cat_data["skills"]) == 27
    assert len(cat_data["interests"]) == 7
    assert len(cat_data["slots"]) == 6
    assert len(cat_data["roles"]) == 6
    assert "Computer Science" in cat_data["departments"]
    assert "Web Application Development" in cat_data["domains"]

def test_rendered_template_dropdowns(client, db_session):
    """Verifies that all HTML pages render complete dropdown options."""
    # 1. Register page has all departments
    reg_page = client.get("/register")
    assert reg_page.status_code == 200
    reg_html = reg_page.get_data(as_text=True)
    for dept in DEPARTMENTS:
        # Check either raw or HTML-escaped string
        escaped_dept = dept.replace("&", "&amp;")
        assert (dept in reg_html) or (escaped_dept in reg_html)

    # 2. Student profile edit has skills, slots, interests, roles, departments
    client.post("/login", data={"email": "student1@college.edu", "password": "Student@123"}, follow_redirects=True)
    prof_page = client.get("/student/profile")
    assert prof_page.status_code == 200
    prof_text = prof_page.get_data(as_text=True)
    assert "Choose Technical Skill" in prof_text
    assert "Python" in prof_text
    assert "React" in prof_text
    assert "Weekday Evenings" in prof_text
    assert "Backend Developer" in prof_text

    # 3. Faculty project create has domains, required skills, required roles
    client.get("/logout")
    client.post("/login", data={"email": "faculty@college.edu", "password": "Faculty@123"}, follow_redirects=True)
    proj_page = client.get("/faculty/projects/new")
    assert proj_page.status_code == 200
    proj_text = proj_page.get_data(as_text=True)
    for dom in DOMAINS:
        escaped_dom = dom.replace("&", "&amp;")
        assert (dom in proj_text) or (escaped_dom in proj_text)
    assert "Machine Learning" in proj_text
    assert "Data &amp; ML Engineer" in proj_text or "Data & ML Engineer" in proj_text

    # 4. Faculty students directory has department filter options
    dir_page = client.get("/faculty/students")
    assert dir_page.status_code == 200
    dir_text = dir_page.get_data(as_text=True)
    assert "Computer Science" in dir_text
    assert "Software Engineering" in dir_text
