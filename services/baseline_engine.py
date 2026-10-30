"""
services/baseline_engine.py
====================================================================
Rule-Based Team Formation Engine (Baseline).
Strictly deterministic, configurable weighted heuristics.
NOT machine learning.
====================================================================
"""

import time
from typing import List, Dict, Any, Tuple
from models.entities import StudentProfile, Project

class RuleBasedTeamEngine:
    DEFAULT_WEIGHTS = {
        "technical_skill": 0.40,
        "interest_domain": 0.20,
        "experience": 0.15,
        "availability": 0.15,
        "preferred_role": 0.10
    }

    @staticmethod
    def validate_weights(weights: Dict[str, float]) -> Dict[str, float]:
        """Validates that weights are non-negative and normalize to 1.0."""
        validated = {}
        for k in RuleBasedTeamEngine.DEFAULT_WEIGHTS:
            val = float(weights.get(k, RuleBasedTeamEngine.DEFAULT_WEIGHTS[k]))
            if val < 0:
                raise ValueError(f"Weight for '{k}' cannot be negative.")
            validated[k] = val

        total = sum(validated.values())
        if total <= 0:
            raise ValueError("Sum of weights must be greater than zero.")

        # Normalize to sum to 1.0
        return {k: round(v / total, 4) for k, v in validated.items()}

    @classmethod
    def calculate_student_score(
        cls, profile: StudentProfile, project: Project, weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculates individual deterministic matching score and component breakdown for a student.
        Each component is normalized to [0, 100].
        """
        # 1. Technical Skill Score
        req_skills = project.required_skills
        if not req_skills:
            skill_score = 70.0  # default when no specific skills requested
            covered_reqs = []
            missing_reqs = []
        else:
            student_skill_map = {ss.skill.name.lower(): ss.proficiency for ss in profile.skills if ss.skill}
            total_req_weight = sum(rs.priority_weight for rs in req_skills) or 1.0
            earned_skill_points = 0.0
            covered_reqs = []
            missing_reqs = []

            for rs in req_skills:
                s_name = rs.skill.name.lower() if rs.skill else ""
                stu_prof = student_skill_map.get(s_name, 0)
                min_prof = rs.min_proficiency
                p_weight = rs.priority_weight

                if stu_prof >= min_prof:
                    # Full or bonus points (up to 1.2x)
                    ratio = min(1.2, stu_prof / min_prof)
                    earned_skill_points += (ratio / 1.2) * p_weight
                    covered_reqs.append(rs.skill.name)
                elif stu_prof > 0:
                    # Partial points for possessing skill below target proficiency
                    ratio = (stu_prof / min_prof) * 0.6
                    earned_skill_points += ratio * p_weight
                    missing_reqs.append(f"{rs.skill.name} (Proficiency {stu_prof}/{min_prof})")
                else:
                    missing_reqs.append(f"{rs.skill.name} (Missing)")

            skill_score = round((earned_skill_points / total_req_weight) * 100.0, 2)

        # 2. Interest and Domain Alignment Score
        student_interests = [si.interest.name.lower() for si in profile.interests if si.interest]
        domain_keywords = project.domain.lower().replace("&", " ").replace("/", " ").split()
        project_desc = (project.description or "").lower()

        interest_matches = 0
        for interest in student_interests:
            # Check domain overlap or project description mentions
            if any(k in interest for k in domain_keywords if len(k) > 3) or interest in project_desc:
                interest_matches += 1

        if not student_interests:
            interest_score = 0.0
        else:
            # Scale score: 1 match = 70, 2 matches = 90, 3+ = 100; baseline 40 for participating
            if interest_matches >= 2:
                interest_score = 100.0
            elif interest_matches == 1:
                interest_score = 80.0
            else:
                interest_score = 40.0

        # 3. Relevant Experience Score
        exp_level_points = {
            "Beginner": 45.0,
            "Intermediate": 80.0,
            "Advanced": 100.0
        }
        base_exp = exp_level_points.get(profile.experience_level, 50.0)
        # Bonus for actual experience years (up to +15)
        years_bonus = min(15.0, (profile.experience_years or 0.0) * 5.0)
        exp_score = min(100.0, round(base_exp + years_bonus, 2))

        # Check project target experience requirement alignment
        if project.experience_level_required != "Any":
            if profile.experience_level == project.experience_level_required:
                exp_score = min(100.0, exp_score + 10.0)

        # 4. Availability Compatibility Score
        # Profiles with multiple slots or 'Flexible / Anytime' receive higher baseline scheduling score
        slots = [sa.slot.slot_name.lower() for sa in profile.availability if sa.slot]
        if any("flexible" in s or "anytime" in s for s in slots):
            avail_score = 100.0
        elif len(slots) >= 3:
            avail_score = 90.0
        elif len(slots) == 2:
            avail_score = 75.0
        elif len(slots) == 1:
            avail_score = 60.0
        else:
            avail_score = 30.0

        # 5. Preferred Role Alignment Score
        proj_roles = [pr.role.name.lower() for pr in project.required_roles if pr.role]
        stu_roles = [spr.role.name.lower() for spr in sorted(profile.preferred_roles, key=lambda x: x.preference_rank) if spr.role]

        if not proj_roles:
            role_score = 75.0
        else:
            role_match_rank = None
            for idx, r in enumerate(stu_roles):
                if r in proj_roles:
                    role_match_rank = idx + 1
                    break

            if role_match_rank == 1:
                role_score = 100.0
            elif role_match_rank == 2:
                role_score = 80.0
            elif role_match_rank == 3:
                role_score = 65.0
            else:
                role_score = 35.0

        # Weighted Total Score (0 - 100)
        total_score = round(
            weights["technical_skill"] * skill_score +
            weights["interest_domain"] * interest_score +
            weights["experience"] * exp_score +
            weights["availability"] * avail_score +
            weights["preferred_role"] * role_score,
            2
        )

        return {
            "total_score": total_score,
            "skill_score": skill_score,
            "interest_score": interest_score,
            "experience_score": exp_score,
            "availability_score": avail_score,
            "role_score": role_score,
            "covered_skills": covered_reqs,
            "missing_skills": missing_reqs
        }

    @classmethod
    def generate_teams(
        cls,
        eligible_students: List[StudentProfile],
        project: Project,
        weights: Dict[str, float] = None,
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        Executes the Rule-Based Baseline team formation algorithm.
        Enforces team size constraints and maximizes complementary skill coverage across teams.
        """
        start_time = time.time()
        weights = cls.validate_weights(weights or cls.DEFAULT_WEIGHTS)
        team_size = project.desired_team_size

        n_students = len(eligible_students)
        if n_students < project.min_team_size:
            return {
                "success": False,
                "error": f"Insufficient eligible students ({n_students}) to form a team of minimum size {project.min_team_size}.",
                "teams": [],
                "unassigned_students": [p.id for p in eligible_students],
                "runtime_seconds": round(time.time() - start_time, 4),
                "method": "baseline"
            }

        # Compute individual scores and breakdowns
        student_scores = {}
        for s in eligible_students:
            student_scores[s.id] = cls.calculate_student_score(s, project, weights)

        # Number of teams to form
        n_teams = n_students // team_size
        if n_teams == 0:
            n_teams = 1
            actual_team_size = n_students
        else:
            actual_team_size = team_size

        # Team structures
        teams = [{"id": i + 1, "name": f"Baseline Team {i + 1}", "members": []} for i in range(n_teams)]

        # Sort students by total baseline score descending
        sorted_students = sorted(eligible_students, key=lambda s: student_scores[s.id]["total_score"], reverse=True)
        assigned_ids = set()

        # Step 1: Seed Anchor Members across teams (top students distributed)
        for i in range(n_teams):
            if i < len(sorted_students):
                anchor = sorted_students[i]
                teams[i]["members"].append(anchor)
                assigned_ids.add(anchor.id)

        # Step 2: Iterative Complementary Fill
        # For remaining slots, assign student that maximizes team's incremental skill/role coverage
        for slot_idx in range(1, actual_team_size):
            for t_idx in range(n_teams):
                team = teams[t_idx]
                if len(team["members"]) >= actual_team_size:
                    continue

                best_candidate = None
                best_marginal_gain = -1.0

                # Current team covered skills
                current_team_skills = set()
                for m in team["members"]:
                    for ss in m.skills:
                        if ss.skill and ss.proficiency >= 2:
                            current_team_skills.add(ss.skill.name.lower())

                for candidate in sorted_students:
                    if candidate.id in assigned_ids:
                        continue

                    # Calculate marginal complementary value
                    new_skills = 0
                    for ss in candidate.skills:
                        if ss.skill and ss.skill.name.lower() not in current_team_skills:
                            new_skills += 1

                    # Combine individual score with complementary skill diversity
                    marginal_val = student_scores[candidate.id]["total_score"] + (new_skills * 15.0)

                    if marginal_val > best_marginal_gain:
                        best_marginal_gain = marginal_val
                        best_candidate = candidate

                if best_candidate:
                    team["members"].append(best_candidate)
                    assigned_ids.add(best_candidate.id)

        # Unassigned students (surplus that does not fill a complete team)
        unassigned = [s for s in eligible_students if s.id not in assigned_ids]

        # Calculate team level aggregates and breakdowns
        formatted_teams = []
        for t in teams:
            team_members_data = []
            team_covered_skills = set()

            for m in t["members"]:
                score_info = student_scores[m.id]
                for ss in m.skills:
                    if ss.skill and ss.proficiency >= 2:
                        team_covered_skills.add(ss.skill.name)

                team_members_data.append({
                    "profile": m,
                    "profile_id": m.id,
                    "student_id": m.student_id,
                    "name": m.user.full_name if m.user else "Student",
                    "matching_score": score_info["total_score"],
                    "score_breakdown": score_info,
                    "cluster_id": None,
                    "cluster_label": "Rule-Based Deterministic Assignment"
                })

            formatted_teams.append({
                "team_index": t["id"],
                "name": t["name"],
                "members": team_members_data,
                "size": len(team_members_data),
                "covered_skills": list(team_covered_skills)
            })

        runtime = round(time.time() - start_time, 4)

        return {
            "success": True,
            "method": "baseline",
            "teams": formatted_teams,
            "weights": weights,
            "n_teams": len(formatted_teams),
            "n_students_assigned": len(assigned_ids),
            "unassigned_students": [
                {
                    "profile_id": u.id,
                    "student_id": u.student_id,
                    "name": u.user.full_name if u.user else "Student",
                    "score": student_scores[u.id]["total_score"]
                }
                for u in unassigned
            ],
            "runtime_seconds": runtime
        }
