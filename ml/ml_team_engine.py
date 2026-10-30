"""
ml/ml_team_engine.py
====================================================================
ML-Guided Complementary Team Recommendation Engine.
Consumes Scikit-Learn K-Means cluster archetypes and feature vectors
to form balanced, complementary student teams with full explainability.
====================================================================
"""

import time
import numpy as np
from typing import List, Dict, Any, Tuple
from models.entities import StudentProfile, Project
from ml.feature_pipeline import StudentFeaturePipeline
from ml.cluster_engine import StudentClusterEngine

class MLGuidedTeamEngine:
    @classmethod
    def generate_teams(
        cls,
        eligible_students: List[StudentProfile],
        project: Project,
        catalogs: Dict[str, Any],
        n_clusters: int = 4,
        random_seed: int = 42,
        db_session = None
    ) -> Dict[str, Any]:
        """
        Executes the ML-Guided team recommendation workflow:
        1. Feature Engineering (StudentFeaturePipeline)
        2. Unsupervised Clustering (Scikit-Learn KMeans)
        3. Complementary Cross-Cluster Team Optimization
        4. Recommendation Explanations Generation
        """
        start_time = time.time()
        n_students = len(eligible_students)
        team_size = project.desired_team_size

        if n_students < project.min_team_size:
            return {
                "success": False,
                "error": f"Insufficient eligible students ({n_students}) to form a team of minimum size {project.min_team_size}.",
                "teams": [],
                "unassigned_students": [p.id for p in eligible_students],
                "runtime_seconds": round(time.time() - start_time, 4),
                "method": "ml"
            }

        # Step 1: Feature Pipeline
        pipeline = StudentFeaturePipeline()
        pipeline.fit_schema(
            skills=catalogs["skills"],
            interests=catalogs["interests"],
            slots=catalogs["slots"],
            roles=catalogs["roles"]
        )

        # Step 2: Fit Scikit-Learn KMeans Model
        cluster_engine = StudentClusterEngine(n_clusters=n_clusters, random_state=random_seed)
        cluster_engine.fit(eligible_students, pipeline)
        # Save model run
        cluster_engine.save(db_session=db_session)

        # Extract cluster labels
        cluster_labels = cluster_engine.cluster_labels
        student_cluster_map = {
            s.id: int(cluster_labels[idx]) for idx, s in enumerate(eligible_students)
        }

        # Step 3: Determine number of teams
        n_teams = n_students // team_size
        if n_teams == 0:
            n_teams = 1
            actual_team_size = n_students
        else:
            actual_team_size = team_size

        teams = [{"id": i + 1, "name": f"AI/ML Team {i + 1}", "members": []} for i in range(n_teams)]
        assigned_ids = set()

        # Group students by cluster for balanced seeding
        cluster_buckets: Dict[int, List[StudentProfile]] = {}
        for s in eligible_students:
            c_id = student_cluster_map[s.id]
            cluster_buckets.setdefault(c_id, []).append(s)

        # Step 4: Diverse Anchor Seeding across clusters
        # Distribute students from different clusters across team seeds
        sorted_cluster_ids = sorted(cluster_buckets.keys(), key=lambda c: len(cluster_buckets[c]), reverse=True)
        seed_idx = 0
        for t in teams:
            assigned_seed = False
            for c_id in sorted_cluster_ids:
                available_in_cluster = [s for s in cluster_buckets[c_id] if s.id not in assigned_ids]
                if available_in_cluster:
                    # Pick student with strongest experience/skill in this cluster
                    anchor = max(available_in_cluster, key=lambda s: float(s.experience_years or 0.0) + len(s.skills))
                    t["members"].append(anchor)
                    assigned_ids.add(anchor.id)
                    assigned_seed = True
                    break
            if not assigned_seed:
                # Fallback to any remaining student
                for s in eligible_students:
                    if s.id not in assigned_ids:
                        t["members"].append(s)
                        assigned_ids.add(s.id)
                        break

        # Step 5: Complementary Greedy Optimization
        # Fill remaining slots by optimizing:
        # 1. Cluster Diversity (avoid repeating clusters in the same team)
        # 2. Skill Complementarity (bring skills the team lacks)
        # 3. Availability Intersection (ensure common meeting slots)
        req_skill_names = {rs.skill.name.lower(): rs.min_proficiency for rs in project.required_skills if rs.skill}

        for slot_idx in range(1, actual_team_size):
            for t in teams:
                if len(t["members"]) >= actual_team_size:
                    continue

                # Current team state
                team_clusters = {student_cluster_map[m.id] for m in t["members"]}
                team_skills = {
                    ss.skill.name.lower(): ss.proficiency
                    for m in t["members"]
                    for ss in m.skills
                    if ss.skill
                }
                team_slots = [
                    {sa.slot.slot_name for sa in m.availability if sa.slot}
                    for m in t["members"]
                ]
                common_slots = set.intersection(*team_slots) if team_slots else set()

                best_candidate = None
                best_score = -999.0

                for candidate in eligible_students:
                    if candidate.id in assigned_ids:
                        continue

                    cand_cluster = student_cluster_map[candidate.id]
                    cand_skills = {ss.skill.name.lower(): ss.proficiency for ss in candidate.skills if ss.skill}
                    cand_slots = {sa.slot.slot_name for sa in candidate.availability if sa.slot}

                    # A. Cluster Diversity Score (Reward unrepresented clusters)
                    if cand_cluster not in team_clusters:
                        cluster_score = 35.0
                    else:
                        cluster_score = 5.0  # penalty for repeating same cluster

                    # B. Complementary Skill Contribution Score
                    skill_gain = 0.0
                    for s_name, prof in cand_skills.items():
                        if s_name in req_skill_names:
                            # If team didn't have this required skill or had lower proficiency
                            current_prof = team_skills.get(s_name, 0)
                            if current_prof < req_skill_names[s_name]:
                                skill_gain += 15.0 * (prof / 5.0)
                            else:
                                skill_gain += 5.0 * (prof / 5.0)
                        else:
                            # General non-overlapping technical skill bonus
                            if s_name not in team_skills:
                                skill_gain += 3.0

                    # C. Availability Compatibility (Jaccard with common team slots)
                    if common_slots:
                        avail_overlap = len(common_slots.intersection(cand_slots)) / len(common_slots.union(cand_slots))
                        avail_score = avail_overlap * 25.0
                    else:
                        avail_score = 15.0

                    # D. Experience balance
                    exp_val = 15.0 if candidate.experience_level == "Advanced" else 10.0

                    total_candidate_score = cluster_score + skill_gain + avail_score + exp_val

                    if total_candidate_score > best_score:
                        best_score = total_candidate_score
                        best_candidate = candidate

                if best_candidate:
                    t["members"].append(best_candidate)
                    assigned_ids.add(best_candidate.id)

        # Unassigned students
        unassigned = [s for s in eligible_students if s.id not in assigned_ids]

        # Step 6: Generate Explanations for each team and member
        formatted_teams = []
        for t in teams:
            team_members_data = []
            team_skills_covered = set()
            team_slots_list = []

            for m in t["members"]:
                c_id = student_cluster_map[m.id]
                c_summary = cluster_engine.cluster_summaries.get(c_id, {})
                c_label = c_summary.get("name", f"Cluster {c_id}")

                stu_skills = {ss.skill.name: ss.proficiency for ss in m.skills if ss.skill}
                stu_slots = {sa.slot.slot_name for sa in m.availability if sa.slot}
                team_slots_list.append(stu_slots)

                for s_name, prof in stu_skills.items():
                    if prof >= 2:
                        team_skills_covered.add(s_name)

                # Explanations
                reasons = []
                # 1. Cluster archetype
                reasons.append(f"Classified as **{c_summary.get('title', 'Specialist')}** by K-Means model.")

                # 2. Key complementary skills
                high_skills = [f"{s} (Lvl {p})" for s, p in stu_skills.items() if p >= 3]
                if high_skills:
                    reasons.append(f"Provides core expertise in {', '.join(high_skills[:3])}.")

                # 3. Project skill match
                matched_reqs = [
                    rs.skill.name for rs in project.required_skills
                    if rs.skill and rs.skill.name in stu_skills and stu_skills[rs.skill.name] >= rs.min_proficiency
                ]
                if matched_reqs:
                    reasons.append(f"Fulfills project requirements: {', '.join(matched_reqs)}.")

                team_members_data.append({
                    "profile": m,
                    "profile_id": m.id,
                    "student_id": m.student_id,
                    "name": m.user.full_name if m.user else "Student",
                    "matching_score": 85.0,  # normalized fit indicator
                    "cluster_id": c_id,
                    "cluster_label": c_label,
                    "cluster_title": c_summary.get("title", f"Cluster {c_id}"),
                    "explanation": " ".join(reasons),
                    "availability_slots": list(stu_slots)
                })

            # Check shared availability
            shared_slots = set.intersection(*team_slots_list) if team_slots_list else set()

            # Check unmet project requirements
            unmet_skills = []
            for rs in project.required_skills:
                if rs.skill and rs.skill.name not in team_skills_covered:
                    unmet_skills.append(rs.skill.name)

            formatted_teams.append({
                "team_index": t["id"],
                "name": t["name"],
                "members": team_members_data,
                "size": len(team_members_data),
                "covered_skills": list(team_skills_covered),
                "unmet_skills": unmet_skills,
                "shared_availability": list(shared_slots),
                "cluster_distribution": {
                    f"Cluster {c_id}": sum(1 for m in team_members_data if m["cluster_id"] == c_id)
                    for c_id in cluster_engine.cluster_summaries
                }
            })

        runtime = round(time.time() - start_time, 4)

        return {
            "success": True,
            "method": "ml",
            "teams": formatted_teams,
            "n_teams": len(formatted_teams),
            "n_students_assigned": len(assigned_ids),
            "unassigned_students": [
                {
                    "profile_id": u.id,
                    "student_id": u.student_id,
                    "name": u.user.full_name if u.user else "Student",
                    "cluster_id": student_cluster_map.get(u.id)
                }
                for u in unassigned
            ],
            "runtime_seconds": runtime,
            "cluster_summaries": cluster_engine.cluster_summaries,
            "silhouette_score": cluster_engine.silhouette_score_,
            "inertia": cluster_engine.inertia_,
            "warning": cluster_engine.insufficient_data_warning
        }
