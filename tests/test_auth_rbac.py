import pytest
from models.entities import User

def test_user_password_hashing(db_session):
    user = User(email="test.hash@college.edu", full_name="Hash Test", role="student")
    user.set_password("Secret123")
    assert user.password_hash != "Secret123"
    assert user.check_password("Secret123") is True
    assert user.check_password("WrongPassword") is False

def test_student_and_faculty_login(client, db_session):
    # Faculty login
    res = client.post("/login", data={"email": "faculty@college.edu", "password": "Faculty@123"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Faculty &amp; Evaluation Dashboard" in res.data or b"Faculty" in res.data

    # Logout
    client.get("/logout", follow_redirects=True)

    # Student login
    res2 = client.post("/login", data={"email": "alex.chen@college.edu", "password": "Student@123"}, follow_redirects=True)
    assert res2.status_code == 200
    assert b"Student Portal" in res2.data

def test_invalid_login(client):
    res = client.post("/login", data={"email": "nonexistent@college.edu", "password": "bad"}, follow_redirects=True)
    assert b"Invalid email or password" in res.data

def test_rbac_access_restrictions(client):
    # Unauthenticated access to faculty dashboard must redirect to login
    client.get("/logout", follow_redirects=True)
    res = client.get("/faculty/dashboard", follow_redirects=True)
    assert b"Please log in" in res.data

    # Log in as student
    client.post("/login", data={"email": "alex.chen@college.edu", "password": "Student@123"}, follow_redirects=True)
    # Student attempting to access faculty dashboard must be denied
    res_denied = client.get("/faculty/dashboard", follow_redirects=True)
    assert b"Access denied: Faculty privileges required" in res_denied.data

def test_registration_duplicate_prevention(client, db_session):
    client.get("/logout", follow_redirects=True)
    # 1. Register a new user
    reg_data = {
        "full_name": "Test Duplication",
        "email": "unique.new.student@college.edu",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "role": "student",
        "student_id": "TEST-DUP-001",
        "department": "Computer Science"
    }
    res = client.post("/register", data=reg_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Registration successful" in res.data

    # 2. Attempt registering again with the exact same email
    res_duplicate = client.post("/register", data=reg_data, follow_redirects=True)
    assert res_duplicate.status_code == 200
    assert b"already exists" in res_duplicate.data

    # 3. Verify user count did not increase on duplicate attempt
    count = db_session.query(User).filter_by(email="unique.new.student@college.edu").count()
    assert count == 1

def test_login_never_inserts_user_and_preserves_session(client, db_session):
    client.get("/logout", follow_redirects=True)
    initial_user_count = db_session.query(User).count()

    # 1. Attempt login with non-existent user
    res_bad = client.post("/login", data={"email": "nonexistent.user.test@college.edu", "password": "SomePassword123"}, follow_redirects=True)
    assert res_bad.status_code == 200
    assert b"Invalid email or password" in res_bad.data

    # 2. Verify NO insert occurred
    assert db_session.query(User).count() == initial_user_count

    # 3. Immediately attempt login with valid existing user
    res_good = client.post("/login", data={"email": "faculty@college.edu", "password": "Faculty@123"}, follow_redirects=True)
    assert res_good.status_code == 200
    assert b"Welcome back" in res_good.data

def test_logout_and_session_cleanup(client):
    # 1. Log in as student
    client.post("/login", data={"email": "student1@college.edu", "password": "Student@123"}, follow_redirects=True)
    res_dash = client.get("/student/dashboard")
    assert res_dash.status_code == 200

    # 2. Test GET /logout
    res_logout_get = client.get("/logout", follow_redirects=True)
    assert res_logout_get.status_code == 200
    assert b"logged out" in res_logout_get.data

    # 3. Verify session is destroyed
    res_dash_after = client.get("/student/dashboard", follow_redirects=True)
    assert b"Please log in" in res_dash_after.data

    # 4. Test POST /logout
    client.post("/login", data={"email": "faculty@college.edu", "password": "Faculty@123"}, follow_redirects=True)
    res_logout_post = client.post("/logout", follow_redirects=True)
    assert res_logout_post.status_code == 200
    assert b"logged out" in res_logout_post.data
