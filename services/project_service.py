from database.db import get_db
from models.entities import (
    Project, ProjectRequiredSkill, ProjectRequiredRole,
    StudentProfile, Skill, Role
)

class ProjectService:
    @staticmethod
    def get_all_projects(status=None, session=None):
        db = session or get_db()
        q = db.query(Project)
        if status:
            q = q.filter_by(status=status)
        return q.order_by(Project.created_at.desc()).all()

    @staticmethod
    def get_project_by_id(project_id, session=None):
        db = session or get_db()
        return db.query(Project).filter_by(id=project_id).first()

    @staticmethod
    def create_project(data, creator_id, session=None):
        """
        Creates a new project with required skills and roles.
        Validates mandatory constraints.
        """
        db = session or get_db()

        title = data.get("title", "").strip()
        domain = data.get("domain", "").strip()
        description = data.get("description", "").strip()
        desired_team_size = int(data.get("desired_team_size", 4))
        min_team_size = int(data.get("min_team_size", max(2, desired_team_size - 1)))
        max_team_size = int(data.get("max_team_size", desired_team_size + 1))
        experience_req = data.get("experience_level_required", "Any")

        if not title:
            raise ValueError("Project title is required.")
        if not domain:
            raise ValueError("Project domain/category is required.")
        if desired_team_size < 2:
            raise ValueError("Desired team size must be at least 2.")
        if not (min_team_size <= desired_team_size <= max_team_size):
            raise ValueError("Team sizes must satisfy: Min Size <= Desired Size <= Max Size.")

        project = Project(
            title=title,
            domain=domain,
            description=description,
            desired_team_size=desired_team_size,
            min_team_size=min_team_size,
            max_team_size=max_team_size,
            experience_level_required=experience_req,
            status="Open",
            created_by=creator_id
        )
        db.add(project)
        db.flush()

        # Add required skills
        skills_input = data.get("required_skills", [])
        for sk in skills_input:
            skill_id = int(sk["skill_id"])
            min_prof = max(1, min(5, int(sk.get("min_proficiency", 2))))
            is_mand = bool(sk.get("is_mandatory", True))
            weight = max(0.1, float(sk.get("priority_weight", 1.0)))
            db.add(ProjectRequiredSkill(
                project_id=project.id,
                skill_id=skill_id,
                min_proficiency=min_prof,
                is_mandatory=is_mand,
                priority_weight=weight
            ))

        # Add required roles
        roles_input = data.get("required_roles", [])
        for rl in roles_input:
            role_id = int(rl["role_id"])
            count = max(1, int(rl.get("count_needed", 1)))
            db.add(ProjectRequiredRole(
                project_id=project.id,
                role_id=role_id,
                count_needed=count
            ))

        db.commit()
        return project

    @staticmethod
    def update_project(project_id, data, session=None):
        db = session or get_db()
        project = db.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project #{project_id} not found.")

        if "title" in data:
            project.title = data["title"].strip()
        if "domain" in data:
            project.domain = data["domain"].strip()
        if "description" in data:
            project.description = data["description"].strip()
        if "desired_team_size" in data:
            project.desired_team_size = int(data["desired_team_size"])
        if "min_team_size" in data:
            project.min_team_size = int(data["min_team_size"])
        if "max_team_size" in data:
            project.max_team_size = int(data["max_team_size"])
        if "experience_level_required" in data:
            project.experience_level_required = data["experience_level_required"]
        if "status" in data:
            project.status = data["status"]

        if not (project.min_team_size <= project.desired_team_size <= project.max_team_size):
            raise ValueError("Team sizes must satisfy: Min Size <= Desired Size <= Max Size.")

        if "required_skills" in data:
            db.query(ProjectRequiredSkill).filter_by(project_id=project.id).delete()
            db.flush()
            for sk in data["required_skills"]:
                db.add(ProjectRequiredSkill(
                    project_id=project.id,
                    skill_id=int(sk["skill_id"]),
                    min_proficiency=max(1, min(5, int(sk.get("min_proficiency", 2)))),
                    is_mandatory=bool(sk.get("is_mandatory", True)),
                    priority_weight=max(0.1, float(sk.get("priority_weight", 1.0)))
                ))

        if "required_roles" in data:
            db.query(ProjectRequiredRole).filter_by(project_id=project.id).delete()
            db.flush()
            for rl in data["required_roles"]:
                db.add(ProjectRequiredRole(
                    project_id=project.id,
                    role_id=int(rl["role_id"]),
                    count_needed=max(1, int(rl.get("count_needed", 1)))
                ))

        db.commit()
        return project

    @staticmethod
    def get_eligible_students(project_id, enforce_profile_completion=True, session=None):
        """
        Determines the eligible student cohort for a project.
        Enforces fair baseline-vs-ML evaluation by providing the identical pool.
        Returns:
            eligible_profiles: list of StudentProfile
            ineligible_info: list of dicts with student_id, name, reason
        """
        db = session or get_db()
        project = db.query(Project).filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project #{project_id} not found.")

        all_profiles = db.query(StudentProfile).all()
        eligible = []
        ineligible = []

        for p in all_profiles:
            # 1. Profile completion check
            if enforce_profile_completion and not p.is_profile_complete:
                ineligible.append({
                    "profile_id": p.id,
                    "student_id": p.student_id,
                    "name": p.user.full_name if p.user else "Unknown",
                    "reason": "Profile incomplete (missing skills, interests, or availability)"
                })
                continue

            # 2. Experience level requirement check if strict
            if project.experience_level_required != "Any":
                exp_rank = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
                req_rank = exp_rank.get(project.experience_level_required, 1)
                stu_rank = exp_rank.get(p.experience_level, 1)
                # We consider students eligible if they are within suitable range (not blocking unless strictly desired)
                # To be flexible, we allow students with >= 1 level below or equal
                if stu_rank < (req_rank - 1):
                    ineligible.append({
                        "profile_id": p.id,
                        "student_id": p.student_id,
                        "name": p.user.full_name if p.user else "Unknown",
                        "reason": f"Experience level ({p.experience_level}) below project prerequisite ({project.experience_level_required})"
                    })
                    continue

            eligible.append(p)

        return eligible, ineligible
