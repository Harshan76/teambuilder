"""
scripts/seed_3_demo_projects.py
====================================================================
Dedicated Idempotent Seeder for the 3 Realistic Demonstration Projects:
1. AI-Powered Student Performance Prediction
2. Smart Campus Management System
3. AI-Powered Resume and Skill Gap Analyzer

Database Safety Guarantee:
- Never drops existing tables.
- Never deletes or modifies existing user accounts or student profiles.
- Completely idempotent: safe to re-run repeatedly without creating duplicates.
====================================================================
"""

import sys
from pathlib import Path

# Add project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.db import db_manager
from database.seed_data import seed_3_demo_projects
from services.project_service import ProjectService

def main():
    print("=" * 70)
    print("  AI GROUP PROJECT TEAM BUILDER - 3 DEMO PROJECTS SEEDER")
    print("=" * 70)
    print("[*] Initializing database connection pool...")
    db_manager.init_db()
    print(f"[*] Connection status: {db_manager.connection_status_message}")

    print("[*] Ensuring database tables exist safely...")
    db_manager.create_all()

    print("[*] Seeding/Updating 3 Demonstration Projects...")
    try:
        session = db_manager.get_session()
        projects = seed_3_demo_projects(session=session)
        print(f"[+] SUCCESS: {len(projects)} Demo Projects seeded successfully!")
        print("-" * 70)
        for p in projects:
            eligible, ineligible = ProjectService.get_eligible_students(p.id, session=session)
            print(f"\n[Project #{p.id}] {p.title}")
            print(f"  Domain:           {p.domain}")
            print(f"  Target Team Size: {p.desired_team_size} members (Min: {p.min_team_size}, Max: {p.max_team_size})")
            print(f"  Eligible Cohort:  {len(eligible)} students (Excluded: {len(ineligible)})")
            print(f"  Expected Teams:   {len(eligible) // p.desired_team_size} teams")
            print("  Required Skills:")
            for req in p.required_skills:
                mand_str = "Mandatory" if req.is_mandatory else "Optional"
                print(f"    - {req.skill.name:<22} (Min Lvl: {req.min_proficiency}, {mand_str}, Weight: {req.priority_weight}x)")
            print("  Required Roles:")
            for r in p.required_roles:
                print(f"    - {r.role.name:<25} (Count: {r.count_needed})")
        print("\n" + "-" * 70)
    except Exception as e:
        print(f"[!] Error seeding projects: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
