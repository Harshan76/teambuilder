from database.db import get_db
from models.entities import (
    User, StudentProfile, Skill, StudentSkill,
    Interest, StudentInterest, AvailabilitySlot, StudentAvailability,
    Role, StudentPreferredRole
)

class StudentService:
    @staticmethod
    def get_profile_by_user_id(user_id, session=None):
        db = session or get_db()
        return db.query(StudentProfile).filter_by(user_id=user_id).first()

    @staticmethod
    def get_profile_by_id(profile_id, session=None):
        db = session or get_db()
        return db.query(StudentProfile).filter_by(id=profile_id).first()

    @staticmethod
    def check_profile_completion(profile):
        """
        Calculates profile completeness.
        Returns (is_complete, missing_requirements, completion_percentage)
        """
        missing = []
        checks_passed = 0
        total_checks = 6

        # 1. Academic ID & Department
        if profile.student_id and profile.department:
            checks_passed += 1
        else:
            missing.append("Student ID and Academic Department")

        # 2. Experience level
        if profile.experience_level:
            checks_passed += 1
        else:
            missing.append("Experience Level")

        # 3. Technical Skills
        if len(profile.skills) >= 1:
            checks_passed += 1
        else:
            missing.append("At least one technical skill with proficiency")

        # 4. Domain Interests
        if len(profile.interests) >= 1:
            checks_passed += 1
        else:
            missing.append("At least one domain interest")

        # 5. Availability Slots
        if len(profile.availability) >= 1:
            checks_passed += 1
        else:
            missing.append("At least one weekly availability time slot")

        # 6. Preferred Roles
        if len(profile.preferred_roles) >= 1:
            checks_passed += 1
        else:
            missing.append("At least one preferred team role")

        is_complete = (len(missing) == 0)
        percentage = int((checks_passed / total_checks) * 100)
        return is_complete, missing, percentage

    @staticmethod
    def update_profile(profile_id, data, session=None):
        """
        Updates student profile fields, technical skills, interests, availability, and roles.
        """
        db = session or get_db()
        profile = db.query(StudentProfile).filter_by(id=profile_id).first()
        if not profile:
            raise ValueError(f"Student profile #{profile_id} not found.")

        # Update core user info if provided
        if "full_name" in data and profile.user:
            profile.user.full_name = data["full_name"].strip()

        # Update profile core fields
        if "student_id" in data:
            profile.student_id = data["student_id"].strip()
        if "department" in data:
            profile.department = data["department"].strip()
        if "experience_level" in data:
            profile.experience_level = data["experience_level"].strip()
        if "experience_years" in data:
            try:
                profile.experience_years = max(0.0, float(data["experience_years"]))
            except (ValueError, TypeError):
                profile.experience_years = 0.0
        if "previous_projects_summary" in data:
            profile.previous_projects_summary = data["previous_projects_summary"].strip()
        if "collaboration_preference" in data:
            profile.collaboration_preference = data["collaboration_preference"].strip()

        # Update Skills
        if "skills" in data:
            # Clear existing skills
            db.query(StudentSkill).filter_by(profile_id=profile.id).delete()
            db.flush()
            skills_input = data["skills"]
            if isinstance(skills_input, dict):
                skills_list = [{"skill_id": k, "proficiency": v} for k, v in skills_input.items()]
            else:
                skills_list = skills_input or []

            seen_skill_ids = set()
            for item in skills_list:
                s_id = None
                prof = 1
                if isinstance(item, dict):
                    if "skill_id" in item and item["skill_id"]:
                        try:
                            s_id = int(item["skill_id"])
                        except (ValueError, TypeError):
                            s_id = None
                    elif "name" in item and item["name"]:
                        sk_obj = db.query(Skill).filter(Skill.name.ilike(item["name"].strip())).first()
                        if sk_obj:
                            s_id = sk_obj.id
                    try:
                        prof = max(1, min(5, int(item.get("proficiency", 1))))
                    except (ValueError, TypeError):
                        prof = 1
                elif item:
                    try:
                        s_id = int(item)
                    except (ValueError, TypeError):
                        s_id = None

                if s_id and s_id not in seen_skill_ids:
                    sk_exists = db.query(Skill).filter_by(id=s_id).first()
                    if sk_exists:
                        seen_skill_ids.add(s_id)
                        db.add(StudentSkill(profile_id=profile.id, skill_id=s_id, proficiency=prof))

        # Update Interests
        if "interest_ids" in data:
            db.query(StudentInterest).filter_by(profile_id=profile.id).delete()
            db.flush()
            for i_id in data["interest_ids"]:
                db.add(StudentInterest(profile_id=profile.id, interest_id=int(i_id)))

        # Update Availability Slots
        if "slot_ids" in data:
            db.query(StudentAvailability).filter_by(profile_id=profile.id).delete()
            db.flush()
            for s_id in data["slot_ids"]:
                db.add(StudentAvailability(profile_id=profile.id, slot_id=int(s_id)))

        # Update Preferred Roles
        if "preferred_roles" in data:
            db.query(StudentPreferredRole).filter_by(profile_id=profile.id).delete()
            db.flush()
            # data["preferred_roles"] is list of {"role_id": int, "preference_rank": int} or list of role_ids
            for rank, r_item in enumerate(data["preferred_roles"], start=1):
                if isinstance(r_item, dict):
                    r_id = int(r_item["role_id"])
                    pref_rank = int(r_item.get("preference_rank", rank))
                else:
                    r_id = int(r_item)
                    pref_rank = rank
                db.add(StudentPreferredRole(profile_id=profile.id, role_id=r_id, preference_rank=pref_rank))

        # Recalculate completeness
        db.flush()
        is_complete, _, _ = StudentService.check_profile_completion(profile)
        profile.is_profile_complete = is_complete

        db.commit()
        return profile

    @staticmethod
    def get_all_students(query=None, department=None, experience=None, complete_only=False, session=None):
        db = session or get_db()
        q = db.query(StudentProfile).join(User)

        if query:
            search = f"%{query.strip()}%"
            q = q.filter((User.full_name.ilike(search)) | (StudentProfile.student_id.ilike(search)) | (User.email.ilike(search)))
        if department:
            q = q.filter(StudentProfile.department == department)
        if experience:
            q = q.filter(StudentProfile.experience_level == experience)
        if complete_only:
            q = q.filter(StudentProfile.is_profile_complete == True)

        return q.order_by(StudentProfile.student_id.asc()).all()

    @staticmethod
    def get_all_catalogs(session=None):
        db = session or get_db()
        skills = db.query(Skill).order_by(Skill.category.asc(), Skill.name.asc()).all()
        interests = db.query(Interest).order_by(Interest.name.asc()).all()
        slots = db.query(AvailabilitySlot).order_by(AvailabilitySlot.id.asc()).all()
        roles = db.query(Role).order_by(Role.id.asc()).all()
        return {
            "skills": skills,
            "interests": interests,
            "slots": slots,
            "roles": roles
        }
