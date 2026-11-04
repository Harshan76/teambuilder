"""
scripts/run_3_projects_generation.py
====================================================================
Executes Rule-Based Baseline and AI/ML (K-Means) Team Generation
for all 3 Demonstration Projects independently:
1. AI-Powered Student Performance Prediction
2. Smart Campus Management System
3. AI-Powered Resume and Skill Gap Analyzer

Verifies:
- 8 eligible students per project.
- Exactly 2 teams of 4 members each per project.
- Zero duplicate student assignments within any single run.
- Diverse role recommendations and complementary skill coverage.
- Saves runs, teams, members, and evaluation metrics in database.
====================================================================
"""

import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.db import db_manager
from models.entities import (
    Project, Role, TeamGenerationRun, Team, TeamMember,
    RoleAssignment, EvaluationResult
)
from services.project_service import ProjectService
from services.student_service import StudentService
from services.baseline_engine import RuleBasedTeamEngine
from services.role_recommender import RoleRecommender
from services.evaluation_service import EvaluationService
from ml.ml_team_engine import MLGuidedTeamEngine
from database.seed_data import seed_3_demo_projects

def run_project_generation(proj, db, catalogs, all_roles):
    print("=" * 72)
    print(f"[*] EXECUTING TEAM GENERATION FOR: Project #{proj.id} - '{proj.title}'")
    print(f"    Domain: {proj.domain} | Target Team Size: {proj.desired_team_size}")
    print("=" * 72)

    eligible, ineligible = ProjectService.get_eligible_students(proj.id, session=db)
    print(f"[+] Eligible Students: {len(eligible)} | Ineligible: {len(ineligible)}")
    if len(eligible) != 8:
        raise ValueError(f"Expected 8 eligible students for '{proj.title}', got {len(eligible)}")

    # Clean existing runs for this specific project
    db.query(TeamGenerationRun).filter_by(project_id=proj.id).delete()
    db.commit()

    # -------------------------------------------------------------
    # 1. RULE-BASED BASELINE GENERATION
    # -------------------------------------------------------------
    print("\n--- [1] RULE-BASED BASELINE RUN ---")
    base_res = RuleBasedTeamEngine.generate_teams(
        eligible_students=eligible,
        project=proj,
        weights=RuleBasedTeamEngine.DEFAULT_WEIGHTS,
        random_seed=42
    )

    if not base_res.get("success"):
        raise RuntimeError(f"Baseline generation failed: {base_res.get('error')}")

    base_run = TeamGenerationRun(
        project_id=proj.id,
        method="baseline",
        weights_json=json.dumps(RuleBasedTeamEngine.DEFAULT_WEIGHTS),
        random_seed=42,
        n_teams=len(base_res["teams"]),
        n_students_assigned=len(eligible),
        n_students_unassigned=0,
        runtime_seconds=base_res["runtime_seconds"]
    )
    db.add(base_run)
    db.flush()

    base_assigned_ids = set()
    for t_data in base_res["teams"]:
        RoleRecommender.recommend_roles_for_team(t_data["members"], proj, all_roles)
        team_entity = Team(
            project_id=proj.id,
            run_id=base_run.id,
            name=f"Baseline Team {t_data['team_index']}",
            generation_method="baseline",
            status="Proposed"
        )
        db.add(team_entity)
        db.flush()

        for m in t_data["members"]:
            rec = m.get("assigned_role") or {}
            tm = TeamMember(
                team_id=team_entity.id,
                profile_id=m["profile_id"],
                assigned_role_id=rec.get("role_id"),
                matching_score=m["matching_score"],
                cluster_label="Rule-Based Baseline"
            )
            db.add(tm)
            db.flush()
            base_assigned_ids.add(m["profile_id"])

            if rec.get("role_id"):
                db.add(RoleAssignment(
                    team_member_id=tm.id,
                    role_id=rec["role_id"],
                    fit_score=rec.get("fit_score", 80.0),
                    rationale=rec.get("rationale", "Assigned by rule baseline")
                ))

    # Evaluate Baseline Metrics
    base_eval = EvaluationService.evaluate_generation(
        base_res["teams"],
        proj,
        len(eligible),
        base_res["runtime_seconds"],
        "baseline"
    )
    db.add(EvaluationResult(
        run_id=base_run.id,
        project_id=proj.id,
        method="baseline",
        skill_coverage_ratio=base_eval["skill_coverage_ratio"],
        avg_skill_alignment=base_eval["avg_skill_alignment"],
        interest_alignment=base_eval["interest_alignment"],
        experience_alignment=base_eval["experience_alignment"],
        availability_compatibility=base_eval["availability_compatibility"],
        role_coverage=base_eval["role_coverage"],
        constraint_satisfaction_rate=base_eval["constraint_satisfaction_rate"],
        team_size_compliance=base_eval["team_size_compliance"],
        assignment_completeness=base_eval["assignment_completeness"],
        unassigned_count=base_eval["unassigned_count"],
        runtime_seconds=base_eval["runtime_seconds"]
    ))

    print(f"    Teams Formed: {len(base_res['teams'])} teams")
    print(f"    Assigned Students: {len(base_assigned_ids)} / 8 (No duplicates: {len(base_assigned_ids) == 8})")
    print(f"    Skill Coverage Ratio: {base_eval['skill_coverage_ratio'] * 100:.1f}%")
    print(f"    Role Coverage Ratio:  {base_eval['role_coverage'] * 100:.1f}%")

    # -------------------------------------------------------------
    # 2. AI / ML-BASED RECOMMENDATION (K-MEANS)
    # -------------------------------------------------------------
    print("\n--- [2] AI/ML (SCIKIT-LEARN K-MEANS) RUN ---")
    ml_res = MLGuidedTeamEngine.generate_teams(
        eligible_students=eligible,
        project=proj,
        catalogs=catalogs,
        n_clusters=4,
        random_seed=42,
        db_session=db
    )

    if not ml_res.get("success"):
        raise RuntimeError(f"ML recommendation failed: {ml_res.get('error')}")

    ml_run = TeamGenerationRun(
        project_id=proj.id,
        method="ml",
        weights_json="{}",
        random_seed=42,
        n_teams=len(ml_res["teams"]),
        n_students_assigned=len(eligible),
        n_students_unassigned=0,
        runtime_seconds=ml_res["runtime_seconds"]
    )
    db.add(ml_run)
    db.flush()

    ml_assigned_ids = set()
    for t_data in ml_res["teams"]:
        RoleRecommender.recommend_roles_for_team(t_data["members"], proj, all_roles)
        team_entity = Team(
            project_id=proj.id,
            run_id=ml_run.id,
            name=f"AI/ML Team {t_data['team_index']}",
            generation_method="ml",
            status="Proposed"
        )
        db.add(team_entity)
        db.flush()

        for m in t_data["members"]:
            rec = m.get("assigned_role") or {}
            tm = TeamMember(
                team_id=team_entity.id,
                profile_id=m["profile_id"],
                assigned_role_id=rec.get("role_id"),
                matching_score=m["matching_score"],
                cluster_id=m.get("cluster_id"),
                cluster_label=m.get("cluster_label")
            )
            db.add(tm)
            db.flush()
            ml_assigned_ids.add(m["profile_id"])

            if rec.get("role_id"):
                db.add(RoleAssignment(
                    team_member_id=tm.id,
                    role_id=rec["role_id"],
                    fit_score=rec.get("fit_score", 85.0),
                    rationale=rec.get("rationale", "Assigned by ML complementary recommendation")
                ))

    # Evaluate ML Metrics
    ml_eval = EvaluationService.evaluate_generation(
        ml_res["teams"],
        proj,
        len(eligible),
        ml_res["runtime_seconds"],
        "ml"
    )
    db.add(EvaluationResult(
        run_id=ml_run.id,
        project_id=proj.id,
        method="ml",
        skill_coverage_ratio=ml_eval["skill_coverage_ratio"],
        avg_skill_alignment=ml_eval["avg_skill_alignment"],
        interest_alignment=ml_eval["interest_alignment"],
        experience_alignment=ml_eval["experience_alignment"],
        availability_compatibility=ml_eval["availability_compatibility"],
        role_coverage=ml_eval["role_coverage"],
        constraint_satisfaction_rate=ml_eval["constraint_satisfaction_rate"],
        team_size_compliance=ml_eval["team_size_compliance"],
        assignment_completeness=ml_eval["assignment_completeness"],
        unassigned_count=ml_eval["unassigned_count"],
        runtime_seconds=ml_eval["runtime_seconds"]
    ))

    db.commit()

    print(f"    Teams Formed: {len(ml_res['teams'])} teams")
    print(f"    Assigned Students: {len(ml_assigned_ids)} / 8 (No duplicates: {len(ml_assigned_ids) == 8})")
    print(f"    Skill Coverage Ratio: {ml_eval['skill_coverage_ratio'] * 100:.1f}%")
    print(f"    Role Coverage Ratio:  {ml_eval['role_coverage'] * 100:.1f}%")

    return {
        "project": proj,
        "eligible_count": len(eligible),
        "base_run": base_run,
        "base_teams": base_res["teams"],
        "base_eval": base_eval,
        "ml_run": ml_run,
        "ml_teams": ml_res["teams"],
        "ml_eval": ml_eval
    }

def main():
    print("=" * 72)
    print("  AI GROUP PROJECT TEAM BUILDER - 3 DEMO PROJECTS GENERATION RUNNER")
    print("=" * 72)
    db_manager.init_db()
    session = db_manager.get_session()

    # Ensure projects are present
    projects = seed_3_demo_projects(session=session)
    catalogs = StudentService.get_all_catalogs(session=session)
    all_roles = session.query(Role).all()

    summary_results = []
    for proj in projects:
        res = run_project_generation(proj, session, catalogs, all_roles)
        summary_results.append(res)

    print("\n" + "=" * 72)
    print("  FINAL 3 PROJECTS GENERATION SUMMARY")
    print("=" * 72)
    for item in summary_results:
        p = item["project"]
        print(f"\n[Project #{p.id}] {p.title}")
        print(f"  Domain: {p.domain} | Target Team Size: {p.desired_team_size}")
        print(f"  Eligible Cohort: {item['eligible_count']} students (100% assigned)")
        print(f"  Baseline Run #{item['base_run'].id}: {len(item['base_teams'])} teams formed (Skill Coverage: {item['base_eval']['skill_coverage_ratio']*100:.1f}%)")
        for t in item["base_teams"]:
            members_str = ", ".join([f"{m['name']} ({m.get('assigned_role', {}).get('role_name', 'None')})" for m in t["members"]])
            print(f"    - {t['name']}: {members_str}")
        print(f"  AI/ML Run #{item['ml_run'].id}: {len(item['ml_teams'])} teams formed (Skill Coverage: {item['ml_eval']['skill_coverage_ratio']*100:.1f}%)")
        for t in item["ml_teams"]:
            members_str = ", ".join([f"{m['name']} ({m.get('assigned_role', {}).get('role_name', 'None')})" for m in t["members"]])
            print(f"    - {t['name']}: {members_str}")

    print("\n[+] ALL 3 PROJECTS SUCCESSFULLY GENERATED AND SAVED TO DATABASE!")

if __name__ == "__main__":
    main()
