"""
services/export_service.py
====================================================================
Export Service. Generates CSV files for final team assignments,
role distribution, evaluation comparisons, and audit reports.
====================================================================
"""

import csv
import io
from typing import List, Dict, Any
from models.entities import Team, TeamMember, Project, EvaluationResult

class ExportService:
    @staticmethod
    def export_teams_csv(teams: List[Team], project: Project) -> str:
        """
        Exports finalized teams, members, assigned roles, matching scores,
        and cluster labels as CSV text.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Project Title", "Project Domain", "Team ID", "Team Name",
            "Generation Method", "Student ID", "Student Name", "Department",
            "Experience Level", "Assigned Role", "Fit/Matching Score",
            "Discovered Cluster Archetype", "Role Rationale"
        ])

        for t in teams:
            for m in t.members:
                profile = m.profile
                user = profile.user if profile else None
                role_assignment = m.role_assignment
                assigned_role_name = m.assigned_role.name if m.assigned_role else (
                    role_assignment.role.name if role_assignment and role_assignment.role else "General Member"
                )
                rationale = role_assignment.rationale if role_assignment else "Standard complementary assignment"

                writer.writerow([
                    project.title,
                    project.domain,
                    t.id,
                    t.name,
                    t.generation_method.upper(),
                    profile.student_id if profile else "N/A",
                    user.full_name if user else "Student",
                    profile.department if profile else "N/A",
                    profile.experience_level if profile else "N/A",
                    assigned_role_name,
                    round(m.matching_score or 0.0, 2),
                    m.cluster_label or "N/A",
                    rationale
                ])

        return output.getvalue()

    @staticmethod
    def export_comparison_csv(comparison_data: Dict[str, Any], project_title: str) -> str:
        """
        Exports the side-by-side metric comparison table between Baseline and ML.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Title block
        writer.writerow(["AI Group Project Team Builder - Evaluation & Comparison Report"])
        writer.writerow(["Project Target", project_title])
        writer.writerow([])

        # Table Header
        writer.writerow([
            "Metric Name", "Metric Description",
            "Rule-Based Baseline (Score)", "Rule-Based Baseline (%)",
            "ML-Guided Approach (Score)", "ML-Guided Approach (%)",
            "Difference (ML - Baseline)", "Outcome Assessment"
        ])

        for row in comparison_data.get("comparison_table", []):
            writer.writerow([
                row["metric_name"],
                row["description"],
                row["baseline_val"],
                f"{row['baseline_pct']}%",
                row["ml_val"],
                f"{row['ml_pct']}%",
                row["difference"],
                row["verdict"]
            ])

        writer.writerow([])
        writer.writerow(["Execution Runtime Notes:"])
        for note in comparison_data.get("commentary", []):
            writer.writerow([note])

        writer.writerow([])
        writer.writerow(["Important Model & Data Limitations:"])
        writer.writerow(["1. Unsupervised K-Means discovers profile archetypes; it does not predict real-world project success without historical outcome data."])
        writer.writerow(["2. Fair evaluation is ensured because both methods operate on the exact same eligible student pool and constraints."])

        return output.getvalue()
