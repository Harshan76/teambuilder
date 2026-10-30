"""
services/role_recommender.py
====================================================================
Role Recommendation Engine.
Matches team members to project roles based on technical skills,
experience, student preferences, and generates explicit rationales.
====================================================================
"""

from typing import List, Dict, Any, Tuple
from models.entities import StudentProfile, Project, Role

ROLE_SKILL_AFFINITY = {
    "Backend Developer": {
        "primary_skills": ["python", "node.js", "java", "flask", "django", "sql"],
        "min_prof": 2
    },
    "Frontend Developer": {
        "primary_skills": ["react", "javascript", "html/css", "vue.js", "typescript"],
        "min_prof": 2
    },
    "Data & ML Engineer": {
        "primary_skills": ["scikit-learn", "pandas", "pytorch", "sql", "tensorflow", "python"],
        "min_prof": 2
    },
    "UI/UX Designer": {
        "primary_skills": ["figma/ui design", "html/css", "javascript"],
        "min_prof": 2
    },
    "QA / Testing Engineer": {
        "primary_skills": ["git/github", "linux", "docker", "python"],
        "min_prof": 2
    },
    "Project Coordinator & Researcher": {
        "primary_skills": ["git/github", "python", "sql"],
        "min_prof": 1
    }
}

class RoleRecommender:
    @staticmethod
    def calculate_role_fitness(profile: StudentProfile, role: Role) -> Tuple[float, str]:
        """
        Calculates a student's suitability score for a given role and generates a clear rationale.
        Score range: [0, 100].
        """
        r_name = role.name
        config = ROLE_SKILL_AFFINITY.get(r_name, {
            "primary_skills": ["python", "javascript", "git/github"],
            "min_prof": 1
        })

        stu_skills = {ss.skill.name.lower(): ss.proficiency for ss in profile.skills if ss.skill}
        pref_roles = {spr.role.name: spr.preference_rank for spr in profile.preferred_roles if spr.role}

        # 1. Technical Skill Fit (up to 50 points)
        relevant_scores = []
        matching_skill_names = []
        for s_name in config["primary_skills"]:
            if s_name in stu_skills:
                prof = stu_skills[s_name]
                relevant_scores.append(prof)
                matching_skill_names.append(f"{s_name.title()} (Lvl {prof})")

        if relevant_scores:
            avg_prof = sum(relevant_scores) / len(relevant_scores)
            skill_points = min(50.0, (avg_prof / 5.0) * 50.0 + (len(relevant_scores) * 3.0))
        else:
            skill_points = 10.0

        # 2. Preference Rank (up to 30 points)
        rank = pref_roles.get(r_name, 0)
        if rank == 1:
            pref_points = 30.0
            pref_note = "Student's 1st preferred role choice."
        elif rank == 2:
            pref_points = 20.0
            pref_note = "Student's 2nd preferred role choice."
        elif rank == 3:
            pref_points = 10.0
            pref_note = "Student's 3rd preferred role choice."
        else:
            pref_points = 0.0
            pref_note = "Not explicitly ranked in student preferences."

        # 3. Experience & Coordination bonus (up to 20 points)
        exp_points = 10.0
        if profile.experience_level == "Advanced":
            exp_points = 20.0
        elif profile.experience_level == "Intermediate":
            exp_points = 15.0

        total_score = min(100.0, round(skill_points + pref_points + exp_points, 1))

        # Generate human-readable rationale
        reasons = []
        if matching_skill_names:
            reasons.append(f"Demonstrated technical proficiency in {', '.join(matching_skill_names[:3])}.")
        reasons.append(pref_note)
        if profile.experience_years and profile.experience_years > 1.5:
            reasons.append(f"Supported by {profile.experience_years} years of academic project experience.")

        rationale = " ".join(reasons)
        return total_score, rationale

    @classmethod
    def recommend_roles_for_team(
        cls,
        team_members: List[Dict[str, Any]],
        project: Project,
        available_roles: List[Role]
    ) -> Dict[str, Any]:
        """
        Assigns the best matching role to each team member using greedy bipartite matching,
        ensuring team role coverage and providing detailed rationales.
        """
        role_map = {r.name: r for r in available_roles}
        req_roles = project.required_roles

        # Target roles list
        target_role_list = []
        for prr in req_roles:
            if prr.role:
                for _ in range(prr.count_needed):
                    target_role_list.append(prr.role)

        # Fallback pool if team members exceed project required roles
        default_roles_order = [
            "Backend Developer", "Frontend Developer", "Data & ML Engineer",
            "QA / Testing Engineer", "UI/UX Designer", "Project Coordinator & Researcher"
        ]
        for name in default_roles_order:
            if len(target_role_list) >= len(team_members):
                break
            if name in role_map and role_map[name] not in target_role_list:
                target_role_list.append(role_map[name])

        # Compute fitness matrix
        # member_idx -> role -> (score, rationale)
        fitness_matrix = []
        for m in team_members:
            m_profile = m["profile"]
            m_scores = {}
            for r in available_roles:
                score, rationale = cls.calculate_role_fitness(m_profile, r)
                m_scores[r.id] = {"score": score, "rationale": rationale, "role": r}
            fitness_matrix.append(m_scores)

        # Greedy maximum weight matching
        assigned_member_indices = set()
        assigned_role_ids = set()
        assignments = {}
        role_gaps = []

        # First pass: try to assign required project roles
        for r in target_role_list:
            best_idx = None
            best_score = -1.0
            best_rationale = ""

            for idx, m in enumerate(team_members):
                if idx in assigned_member_indices:
                    continue
                score_info = fitness_matrix[idx].get(r.id)
                if score_info and score_info["score"] > best_score:
                    best_score = score_info["score"]
                    best_idx = idx
                    best_rationale = score_info["rationale"]

            if best_idx is not None and best_score >= 35.0:
                assignments[best_idx] = {
                    "role_id": r.id,
                    "role_name": r.name,
                    "fit_score": best_score,
                    "rationale": best_rationale
                }
                assigned_member_indices.add(best_idx)
                assigned_role_ids.add(r.id)
            else:
                role_gaps.append(f"No strong candidate found for required role: {r.name}")

        # Second pass: assign remaining unassigned members to their best suitable unassigned role
        for idx, m in enumerate(team_members):
            if idx in assigned_member_indices:
                continue

            best_r_id = None
            best_r_name = ""
            best_score = -1.0
            best_rationale = ""

            for r in available_roles:
                score_info = fitness_matrix[idx].get(r.id)
                # prefer roles not already in team
                novelty_bonus = 15.0 if r.id not in assigned_role_ids else 0.0
                curr_score = score_info["score"] + novelty_bonus

                if curr_score > best_score:
                    best_score = score_info["score"]
                    best_r_id = r.id
                    best_r_name = r.name
                    best_rationale = score_info["rationale"]

            assignments[idx] = {
                "role_id": best_r_id,
                "role_name": best_r_name,
                "fit_score": max(30.0, best_score),
                "rationale": best_rationale or "Assigned based on complementary team distribution."
            }
            assigned_member_indices.add(idx)
            assigned_role_ids.add(best_r_id)

        # Attach assignments back to members
        for idx, m in enumerate(team_members):
            m["assigned_role"] = assignments.get(idx)

        return {
            "assignments": assignments,
            "role_gaps": role_gaps
        }
