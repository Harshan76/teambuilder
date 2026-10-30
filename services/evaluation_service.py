"""
services/evaluation_service.py
====================================================================
Objective Evaluation & Side-by-Side Comparison Module.
Computes mathematically defined observable assignment quality metrics.
No hardcoded percentages. No fabricated success claims.
====================================================================
"""

from typing import List, Dict, Any, Tuple
from models.entities import Project, StudentProfile

class EvaluationService:
    @classmethod
    def evaluate_generation(
        cls,
        teams_data: List[Dict[str, Any]],
        project: Project,
        total_eligible_count: int,
        runtime_seconds: float,
        method: str
    ) -> Dict[str, Any]:
        """
        Computes the complete suite of observable assignment metrics for a generated team set.
        Returns normalized float metrics [0.0 - 1.0], percentages, and diagnostic notes.
        """
        n_teams = len(teams_data)
        if n_teams == 0:
            return {
                "method": method,
                "n_teams": 0,
                "n_students_assigned": 0,
                "skill_coverage_ratio": 0.0,
                "avg_skill_alignment": 0.0,
                "interest_alignment": 0.0,
                "experience_alignment": 0.0,
                "availability_compatibility": 0.0,
                "role_coverage": 0.0,
                "constraint_satisfaction_rate": 0.0,
                "team_size_compliance": 0.0,
                "assignment_completeness": 0.0,
                "unassigned_count": total_eligible_count,
                "runtime_seconds": runtime_seconds,
                "analysis_notes": ["No teams could be formed with given constraints."]
            }

        all_assigned_members = [m for t in teams_data for m in t.get("members", [])]
        n_assigned = len(all_assigned_members)
        req_skills = project.required_skills
        req_roles = project.required_roles
        desired_size = project.desired_team_size

        # 1. Skill Coverage Ratio
        # Fraction of project required skills covered by at least one member with >= min_proficiency in each team
        team_skill_coverages = []
        for t in teams_data:
            members = t.get("members", [])
            covered_in_team = 0
            for rs in req_skills:
                s_name = rs.skill.name.lower() if rs.skill else ""
                has_proficient_member = False
                for m in members:
                    prof_skills = {ss.skill.name.lower(): ss.proficiency for ss in m["profile"].skills if ss.skill}
                    if prof_skills.get(s_name, 0) >= rs.min_proficiency:
                        has_proficient_member = True
                        break
                if has_proficient_member:
                    covered_in_team += 1

            team_ratio = covered_in_team / len(req_skills) if req_skills else 1.0
            team_skill_coverages.append(team_ratio)

        avg_skill_coverage_ratio = round(sum(team_skill_coverages) / n_teams, 4)

        # 2. Average Student-Project Skill Alignment
        # Average depth of required skills possessed by each assigned student
        student_alignments = []
        for m in all_assigned_members:
            stu_skills = {ss.skill.name.lower(): ss.proficiency for ss in m["profile"].skills if ss.skill}
            if not req_skills:
                student_alignments.append(0.8)
            else:
                align_sum = 0.0
                for rs in req_skills:
                    s_name = rs.skill.name.lower() if rs.skill else ""
                    p = stu_skills.get(s_name, 0)
                    align_sum += min(1.0, p / float(rs.min_proficiency))
                student_alignments.append(align_sum / len(req_skills))

        avg_student_skill_alignment = round(sum(student_alignments) / len(student_alignments), 4) if student_alignments else 0.0

        # 3. Interest & Domain Alignment
        # Percentage of assigned students whose recorded interests match the project domain keywords
        domain_keywords = set(project.domain.lower().replace("&", " ").replace("/", " ").split())
        matched_interest_students = 0
        for m in all_assigned_members:
            interests = [si.interest.name.lower() for si in m["profile"].interests if si.interest]
            has_match = any(any(k in intr for k in domain_keywords if len(k) > 3) for intr in interests)
            if has_match:
                matched_interest_students += 1

        interest_alignment = round(matched_interest_students / n_assigned, 4) if n_assigned > 0 else 0.0

        # 4. Experience Alignment
        exp_rank = {"Beginner": 0.40, "Intermediate": 0.75, "Advanced": 1.00}
        exp_scores = [exp_rank.get(m["profile"].experience_level, 0.50) for m in all_assigned_members]
        experience_alignment = round(sum(exp_scores) / len(exp_scores), 4) if exp_scores else 0.0

        # 5. Availability Compatibility
        # Average pairwise Jaccard similarity of availability slots within each team
        team_avail_compatibilities = []
        for t in teams_data:
            members = t.get("members", [])
            if len(members) < 2:
                team_avail_compatibilities.append(1.0)
                continue

            pairwise_sims = []
            for i in range(len(members)):
                slots_i = {sa.slot.slot_name for sa in members[i]["profile"].availability if sa.slot}
                for j in range(i + 1, len(members)):
                    slots_j = {sa.slot.slot_name for sa in members[j]["profile"].availability if sa.slot}
                    union = slots_i.union(slots_j)
                    if not union:
                        pairwise_sims.append(0.5)
                    else:
                        jaccard = len(slots_i.intersection(slots_j)) / len(union)
                        pairwise_sims.append(jaccard)

            team_avail_compatibilities.append(sum(pairwise_sims) / len(pairwise_sims) if pairwise_sims else 1.0)

        availability_compatibility = round(sum(team_avail_compatibilities) / n_teams, 4)

        # 6. Role Coverage Ratio
        team_role_coverages = []
        for t in teams_data:
            members = t.get("members", [])
            assigned_roles_in_team = set()
            for m in members:
                role_info = m.get("assigned_role")
                if role_info and role_info.get("role_name"):
                    assigned_roles_in_team.add(role_info["role_name"].lower())

            if not req_roles:
                team_role_coverages.append(1.0)
            else:
                covered = sum(1 for rr in req_roles if rr.role and rr.role.name.lower() in assigned_roles_in_team)
                team_role_coverages.append(covered / len(req_roles))

        role_coverage = round(sum(team_role_coverages) / n_teams, 4)

        # 7. Team-Size Compliance
        exact_size_teams = sum(1 for t in teams_data if len(t.get("members", [])) == desired_size)
        team_size_compliance = round(exact_size_teams / n_teams, 4)

        # 8. Constraint Satisfaction Rate
        # Hard constraints: team size within [min_team_size, max_team_size] and mandatory skills covered
        valid_teams = 0
        mandatory_skills = [rs for rs in req_skills if rs.is_mandatory]
        for t in teams_data:
            m_count = len(t.get("members", []))
            size_ok = (project.min_team_size <= m_count <= project.max_team_size)

            mand_ok = True
            for ms in mandatory_skills:
                ms_name = ms.skill.name.lower() if ms.skill else ""
                has_it = any(
                    any(ss.skill.name.lower() == ms_name and ss.proficiency >= ms.min_proficiency
                        for ss in m["profile"].skills if ss.skill)
                    for m in t.get("members", [])
                )
                if not has_it:
                    mand_ok = False
                    break

            if size_ok and mand_ok:
                valid_teams += 1

        constraint_satisfaction_rate = round(valid_teams / n_teams, 4)

        # 9. Assignment Completeness
        assignment_completeness = round(n_assigned / total_eligible_count, 4) if total_eligible_count > 0 else 0.0
        unassigned_count = total_eligible_count - n_assigned

        return {
            "method": method,
            "n_teams": n_teams,
            "n_students_assigned": n_assigned,
            "total_eligible_count": total_eligible_count,
            "unassigned_count": unassigned_count,
            "skill_coverage_ratio": avg_skill_coverage_ratio,
            "avg_skill_alignment": avg_student_skill_alignment,
            "interest_alignment": interest_alignment,
            "experience_alignment": experience_alignment,
            "availability_compatibility": availability_compatibility,
            "role_coverage": role_coverage,
            "constraint_satisfaction_rate": constraint_satisfaction_rate,
            "team_size_compliance": team_size_compliance,
            "assignment_completeness": assignment_completeness,
            "runtime_seconds": runtime_seconds
        }

    @classmethod
    def compare_evaluations(cls, baseline_eval: Dict[str, Any], ml_eval: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produces side-by-side metric comparison and honest diagnostic commentary.
        """
        metrics = [
            ("Skill Coverage Ratio", "skill_coverage_ratio", "Measures fraction of required project skills covered by >=1 proficient team member."),
            ("Avg Skill Alignment", "avg_skill_alignment", "Measures average individual student alignment with project skill requirements."),
            ("Interest Alignment", "interest_alignment", "Measures fraction of students whose interests match project domain."),
            ("Experience Alignment", "experience_alignment", "Measures overall experience level suitability across assigned students."),
            ("Availability Compatibility", "availability_compatibility", "Pairwise Jaccard similarity of weekly schedule slots within teams."),
            ("Role Coverage", "role_coverage", "Fraction of required project roles fulfilled by specialized members."),
            ("Constraint Satisfaction", "constraint_satisfaction_rate", "Fraction of teams satisfying mandatory skill and size bounds."),
            ("Team Size Compliance", "team_size_compliance", "Percentage of teams matching exact target team size."),
            ("Assignment Completeness", "assignment_completeness", "Percentage of eligible student cohort successfully assigned.")
        ]

        table = []
        for name, key, desc in metrics:
            b_val = baseline_eval.get(key, 0.0)
            m_val = ml_eval.get(key, 0.0)
            diff = round(m_val - b_val, 4)

            # Honest comparison note
            if abs(diff) < 0.02:
                verdict = "Comparable Performance"
            elif diff > 0:
                verdict = f"ML-Guided leads by +{round(diff * 100, 1)}%"
            else:
                verdict = f"Rule-Based Baseline leads by +{round(abs(diff) * 100, 1)}%"

            table.append({
                "metric_name": name,
                "description": desc,
                "baseline_val": b_val,
                "baseline_pct": round(b_val * 100, 1),
                "ml_val": m_val,
                "ml_pct": round(m_val * 100, 1),
                "difference": diff,
                "verdict": verdict
            })

        # Diagnostic commentary
        commentary = []
        b_skill = baseline_eval.get("skill_coverage_ratio", 0)
        m_skill = ml_eval.get("skill_coverage_ratio", 0)
        if m_skill > b_skill:
            commentary.append("The ML-guided complementary optimization successfully diversified cluster archetypes, yielding broader collective skill coverage across teams.")
        elif b_skill > m_skill:
            commentary.append("The rule-based baseline direct skill weighting prioritized immediate target proficiency match higher on individual required skills.")
        else:
            commentary.append("Both approaches achieved identical aggregate skill coverage on the current student distribution.")

        b_time = baseline_eval.get("runtime_seconds", 0)
        m_time = ml_eval.get("runtime_seconds", 0)
        commentary.append(f"Runtime: Baseline took {b_time:.4f}s vs ML took {m_time:.4f}s (including K-Means training & feature extraction).")

        return {
            "comparison_table": table,
            "commentary": commentary,
            "baseline": baseline_eval,
            "ml": ml_eval
        }
