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

    old_team_name = member.team.name
    member.team_id = target_team.id
    db.commit()

    return jsonify({
        "success": True,
        "message": f"Successfully moved {member.profile.user.full_name} from {old_team_name} to {target_team.name}."
    })

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
