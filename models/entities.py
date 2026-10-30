from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, UniqueConstraint, Enum
)
from sqlalchemy.orm import relationship
from database.db import Base
from werkzeug.security import generate_password_hash, check_password_hash

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(191), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="student")  # 'student' or 'faculty'
    full_name = Column(String(150), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    projects_created = relationship("Project", back_populates="creator")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login interface properties
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def is_faculty(self):
        return self.role == "faculty"

    def is_student(self):
        return self.role == "student"


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    student_id = Column(String(50), unique=True, nullable=False)  # e.g., 'STU2026-001'
    department = Column(String(100), nullable=False, default="Computer Science")
    experience_level = Column(String(50), nullable=False, default="Beginner")  # 'Beginner', 'Intermediate', 'Advanced'
    experience_years = Column(Float, default=0.0)
    previous_projects_summary = Column(Text, nullable=True)
    collaboration_preference = Column(String(100), default="Flexible / Balanced")
    is_profile_complete = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
    skills = relationship("StudentSkill", back_populates="profile", cascade="all, delete-orphan")
    interests = relationship("StudentInterest", back_populates="profile", cascade="all, delete-orphan")
    availability = relationship("StudentAvailability", back_populates="profile", cascade="all, delete-orphan")
    preferred_roles = relationship("StudentPreferredRole", back_populates="profile", cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="profile", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # 'Frontend', 'Backend', 'Data/AI', 'DevOps', 'Mobile', etc.

    student_skills = relationship("StudentSkill", back_populates="skill")
    project_requirements = relationship("ProjectRequiredSkill", back_populates="skill")


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    proficiency = Column(Integer, nullable=False, default=1)  # 1 to 5

    __table_args__ = (
        UniqueConstraint("profile_id", "skill_id", name="uk_student_skill"),
    )

    profile = relationship("StudentProfile", back_populates="skills")
    skill = relationship("Skill", back_populates="student_skills")


class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    student_interests = relationship("StudentInterest", back_populates="interest")


class StudentInterest(Base):
    __tablename__ = "student_interests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    interest_id = Column(Integer, ForeignKey("interests.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("profile_id", "interest_id", name="uk_student_interest"),
    )

    profile = relationship("StudentProfile", back_populates="interests")
    interest = relationship("Interest", back_populates="student_interests")


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_name = Column(String(100), unique=True, nullable=False)
    time_range = Column(String(100), nullable=True)

    student_availabilities = relationship("StudentAvailability", back_populates="slot")


class StudentAvailability(Base):
    __tablename__ = "student_availability"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    slot_id = Column(Integer, ForeignKey("availability_slots.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("profile_id", "slot_id", name="uk_student_availability"),
    )

    profile = relationship("StudentProfile", back_populates="availability")
    slot = relationship("AvailabilitySlot", back_populates="student_availabilities")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    key_skills_summary = Column(String(255), nullable=True)

    preferred_by_students = relationship("StudentPreferredRole", back_populates="role")
    required_in_projects = relationship("ProjectRequiredRole", back_populates="role")
    assigned_members = relationship("TeamMember", back_populates="assigned_role")


class StudentPreferredRole(Base):
    __tablename__ = "student_preferred_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    preference_rank = Column(Integer, nullable=False, default=1)  # 1 = top choice, 2 = 2nd choice, etc.

    __table_args__ = (
        UniqueConstraint("profile_id", "role_id", name="uk_student_role"),
    )

    profile = relationship("StudentProfile", back_populates="preferred_roles")
    role = relationship("Role", back_populates="preferred_by_students")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(100), nullable=False)
    desired_team_size = Column(Integer, nullable=False, default=4)
    min_team_size = Column(Integer, nullable=False, default=3)
    max_team_size = Column(Integer, nullable=False, default=5)
    experience_level_required = Column(String(50), nullable=False, default="Any")  # 'Beginner', 'Intermediate', 'Advanced', 'Any'
    status = Column(String(50), nullable=False, default="Open")  # 'Draft', 'Open', 'Formed', 'Finalized'
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="projects_created")
    required_skills = relationship("ProjectRequiredSkill", back_populates="project", cascade="all, delete-orphan")
    required_roles = relationship("ProjectRequiredRole", back_populates="project", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")
    generation_runs = relationship("TeamGenerationRun", back_populates="project", cascade="all, delete-orphan")


class ProjectRequiredSkill(Base):
    __tablename__ = "project_required_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    min_proficiency = Column(Integer, nullable=False, default=2)  # 1 to 5
    is_mandatory = Column(Boolean, nullable=False, default=True)
    priority_weight = Column(Float, nullable=False, default=1.0)

    __table_args__ = (
        UniqueConstraint("project_id", "skill_id", name="uk_project_skill"),
    )

    project = relationship("Project", back_populates="required_skills")
    skill = relationship("Skill", back_populates="project_requirements")


class ProjectRequiredRole(Base):
    __tablename__ = "project_required_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    count_needed = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("project_id", "role_id", name="uk_project_role"),
    )

    project = relationship("Project", back_populates="required_roles")
    role = relationship("Role", back_populates="required_in_projects")


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    algorithm = Column(String(50), nullable=False, default="K-Means")
    n_clusters = Column(Integer, nullable=False)
    silhouette_score = Column(Float, nullable=True)
    inertia = Column(Float, nullable=True)
    n_samples = Column(Integer, nullable=False)
    features_json = Column(Text, nullable=True)
    model_file_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    trained_at = Column(DateTime, default=datetime.utcnow)


class TeamGenerationRun(Base):
    __tablename__ = "team_generation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    method = Column(String(50), nullable=False)  # 'baseline' or 'ml'
    weights_json = Column(Text, nullable=True)
    random_seed = Column(Integer, default=42)
    n_teams = Column(Integer, nullable=False)
    n_students_assigned = Column(Integer, nullable=False)
    n_students_unassigned = Column(Integer, nullable=False, default=0)
    runtime_seconds = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="generation_runs")
    teams = relationship("Team", back_populates="generation_run")
    evaluation = relationship("EvaluationResult", back_populates="generation_run", uselist=False, cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    generation_method = Column(String(50), nullable=False)  # 'baseline', 'ml', or 'manual'
    run_id = Column(Integer, ForeignKey("team_generation_runs.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="Proposed")  # 'Proposed', 'Approved', 'Finalized'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="teams")
    generation_run = relationship("TeamGenerationRun", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    assigned_role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    matching_score = Column(Float, default=0.00)
    cluster_id = Column(Integer, nullable=True)
    cluster_label = Column(String(100), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("team_id", "profile_id", name="uk_team_student"),
    )

    # Relationships
    team = relationship("Team", back_populates="members")
    profile = relationship("StudentProfile", back_populates="team_memberships")
    assigned_role = relationship("Role", back_populates="assigned_members")
    role_assignment = relationship("RoleAssignment", back_populates="team_member", uselist=False, cascade="all, delete-orphan")


class RoleAssignment(Base):
    __tablename__ = "role_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_member_id = Column(Integer, ForeignKey("team_members.id", ondelete="CASCADE"), unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    fit_score = Column(Float, nullable=False, default=0.0)
    rationale = Column(Text, nullable=False)
    is_overridden = Column(Boolean, nullable=False, default=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    team_member = relationship("TeamMember", back_populates="role_assignment")
    role = relationship("Role")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("team_generation_runs.id", ondelete="CASCADE"), unique=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    method = Column(String(50), nullable=False)  # 'baseline' or 'ml'
    skill_coverage_ratio = Column(Float, nullable=False)
    avg_skill_alignment = Column(Float, nullable=False)
    interest_alignment = Column(Float, nullable=False)
    experience_alignment = Column(Float, nullable=False)
    availability_compatibility = Column(Float, nullable=False)
    role_coverage = Column(Float, nullable=False)
    constraint_satisfaction_rate = Column(Float, nullable=False)
    team_size_compliance = Column(Float, nullable=False)
    assignment_completeness = Column(Float, nullable=False)
    unassigned_count = Column(Integer, nullable=False, default=0)
    runtime_seconds = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    generation_run = relationship("TeamGenerationRun", back_populates="evaluation")
