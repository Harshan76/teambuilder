from flask import Blueprint, request, jsonify
from database.db import get_db
from models.entities import TeamMember, Team, RoleAssignment, Role
from services.auth_service import login_required, faculty_required

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/team/reassign", methods=["POST"])
@login_required
@faculty_required
def reassign_member():
    data = request.get_json() or {}
    member_id = data.get("member_id")
    target_team_id = data.get("target_team_id")

    if not member_id or not target_team_id:
        return jsonify({"success": False, "error": "member_id and target_team_id required"}), 400

    db = get_db()
    member = db.query(TeamMember).filter_by(id=member_id).first()
    target_team = db.query(Team).filter_by(id=target_team_id).first()

    if not member or not target_team:
        return jsonify({"success": False, "error": "Member or Target Team not found"}), 404

    # Check project match
    if member.team.project_id != target_team.project_id:
        return jsonify({"success": False, "error": "Cannot reassign between different projects"}), 400

    try:
        old_team_name = member.team.name
        member.team_id = target_team.id
        db.commit()
        return jsonify({
            "success": True,
            "message": f"Successfully moved {member.profile.user.full_name} from {old_team_name} to {target_team.name}."
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": f"Database error during reassignment: {str(e)}"}), 500

@api_bp.route("/team/override-role", methods=["POST"])
@login_required
@faculty_required
def override_role():
    data = request.get_json() or {}
    member_id = data.get("member_id")
    role_id = data.get("role_id")

    if not member_id or not role_id:
        return jsonify({"success": False, "error": "member_id and role_id required"}), 400

    db = get_db()
    member = db.query(TeamMember).filter_by(id=member_id).first()
    role = db.query(Role).filter_by(id=role_id).first()

    if not member or not role:
        return jsonify({"success": False, "error": "Member or Role not found"}), 404

    try:
        member.assigned_role_id = role.id

        if member.role_assignment:
            member.role_assignment.role_id = role.id
            member.role_assignment.is_overridden = True
            member.role_assignment.rationale = f"Role manually assigned by faculty review to {role.name}."
        else:
            new_assign = RoleAssignment(
                team_member_id=member.id,
                role_id=role.id,
                fit_score=80.0,
                rationale=f"Role manually assigned by faculty review to {role.name}.",
                is_overridden=True
            )
            db.add(new_assign)

        db.commit()

        return jsonify({
            "success": True,
            "message": f"Assigned role for {member.profile.user.full_name} updated to {role.name}."
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": f"Database error during role override: {str(e)}"}), 500

@api_bp.route("/student/skills", methods=["GET"])
@login_required
def get_student_skills():
    """Returns the full catalog of technical skills and the student's current proficiencies."""
    from services.auth_service import get_current_user
    from models.entities import Skill, StudentProfile, StudentSkill
    user = get_current_user()
    db = get_db()
    
    all_skills = db.query(Skill).order_by(Skill.category.asc(), Skill.name.asc()).all()
    if not all_skills:
        try:
            from database.seed_data import ensure_master_catalogs
            ensure_master_catalogs(session=db)
            all_skills = db.query(Skill).order_by(Skill.category.asc(), Skill.name.asc()).all()
        except Exception:
            pass

    skills_catalog = [{"id": s.id, "name": s.name, "category": s.category} for s in all_skills]
    
    student_skills = []
    if user and user.profile:
        for ss in user.profile.skills:
            student_skills.append({
                "skill_id": ss.skill_id,
                "name": ss.skill.name if ss.skill else "",
                "category": ss.skill.category if ss.skill else "",
                "proficiency": ss.proficiency
            })
            
    return jsonify({
        "success": True,
        "catalog": skills_catalog,
        "selected_skills": student_skills
    })

@api_bp.route("/catalogs", methods=["GET"])
@login_required
def get_all_catalogs_api():
    """Returns all reference master catalogs including skills, interests, slots, roles, departments, and domains."""
    from services.student_service import StudentService
    from models.constants import DEPARTMENTS, DOMAINS, EXPERIENCE_LEVELS, PROFICIENCY_LEVELS
    db = get_db()
    cat = StudentService.get_all_catalogs(session=db)
    return jsonify({
        "success": True,
        "skills": [{"id": s.id, "name": s.name, "category": s.category} for s in cat["skills"]],
        "interests": [{"id": i.id, "name": i.name, "description": i.description} for i in cat["interests"]],
        "slots": [{"id": sl.id, "slot_name": sl.slot_name, "time_range": sl.time_range} for sl in cat["slots"]],
        "roles": [{"id": r.id, "name": r.name, "description": r.description, "key_skills_summary": r.key_skills_summary} for r in cat["roles"]],
        "departments": DEPARTMENTS,
        "domains": DOMAINS,
        "experience_levels": EXPERIENCE_LEVELS,
        "proficiency_levels": PROFICIENCY_LEVELS
    })

@api_bp.route("/student/skills", methods=["POST"])
@login_required
def save_student_skill():
    """Adds or updates a student technical skill with verified proficiency level."""
    from services.auth_service import get_current_user
    from models.entities import Skill, StudentProfile, StudentSkill
    user = get_current_user()
    if not user or not user.profile:
        return jsonify({"success": False, "error": "Student profile not found"}), 404

    data = request.get_json() or {}
    skill_id = data.get("skill_id")
    proficiency = data.get("proficiency", 3)

    if not skill_id:
        return jsonify({"success": False, "error": "skill_id is required"}), 400

    try:
        skill_id = int(skill_id)
        proficiency = max(1, min(5, int(proficiency)))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid skill_id or proficiency format"}), 400

    db = get_db()
    skill = db.query(Skill).filter_by(id=skill_id).first()
    if not skill:
        return jsonify({"success": False, "error": "Skill not found in catalog"}), 404

    try:
        existing = db.query(StudentSkill).filter_by(profile_id=user.profile.id, skill_id=skill_id).first()
        if existing:
            existing.proficiency = proficiency
        else:
            new_ss = StudentSkill(profile_id=user.profile.id, skill_id=skill_id, proficiency=proficiency)
            db.add(new_ss)
        
        # Check completeness
        from services.student_service import StudentService
        is_complete, _, _ = StudentService.check_profile_completion(user.profile)
        user.profile.is_profile_complete = is_complete

        db.commit()
        return jsonify({
            "success": True,
            "message": f"Skill '{skill.name}' saved with proficiency Level {proficiency}.",
            "skill": {
                "skill_id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "proficiency": proficiency
            }
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": f"Database error saving skill: {str(e)}"}), 500

@api_bp.route("/student/skills/<int:skill_id>", methods=["DELETE"])
@login_required
def delete_student_skill(skill_id):
    """Removes a technical skill from the student's profile."""
    from services.auth_service import get_current_user
    from models.entities import StudentSkill
    user = get_current_user()
    if not user or not user.profile:
        return jsonify({"success": False, "error": "Student profile not found"}), 404

    db = get_db()
    try:
        existing = db.query(StudentSkill).filter_by(profile_id=user.profile.id, skill_id=skill_id).first()
        if not existing:
            return jsonify({"success": False, "error": "Skill not currently assigned to profile"}), 404

        db.delete(existing)
        
        from services.student_service import StudentService
        is_complete, _, _ = StudentService.check_profile_completion(user.profile)
        user.profile.is_profile_complete = is_complete

        db.commit()
        return jsonify({
            "success": True,
            "message": "Skill removed successfully."
        })
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "error": f"Database error deleting skill: {str(e)}"}), 500
