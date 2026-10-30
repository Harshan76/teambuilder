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
