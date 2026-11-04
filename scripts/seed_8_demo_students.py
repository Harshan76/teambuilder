"""
scripts/seed_8_demo_students.py
====================================================================
Dedicated Idempotent Seeder for 8 Complete Demo Student Profiles
and Demonstration Showcase Project.

Populates Aiven MySQL / Local Database with:
- 8 Unique Demo Student Accounts (demo.student1@college.edu to demo.student8@college.edu)
- Unique IDs: DEMO-STU-001 to DEMO-STU-008
- Complete multi-disciplinary skill proficiencies, interests, roles, availability
- 100% profile completeness & guaranteed team-generation eligibility
- 1 Dedicated Showcase Project: "[DEMO] AI Multi-Agent Collaboration Hub" (Target size: 4)

Database Safety Guarantee:
- Never drops existing tables.
- Never deletes or modifies existing real student or faculty accounts.
- Completely idempotent: safe to re-run repeatedly without creating duplicates.
====================================================================
"""

import sys
from pathlib import Path

# Add project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.db import db_manager
from database.seed_data import seed_8_demo_students

def main():
    print("=" * 68)
    print("  AI GROUP PROJECT TEAM BUILDER - 8 DEMO STUDENT PROFILES SEEDER")
    print("=" * 68)
    print("[*] Initializing database connection pool...")
    db_manager.init_db()
    print(f"[*] Connection status: {db_manager.connection_status_message}")

    print("[*] Ensuring database tables exist safely...")
    db_manager.create_all()

    print("[*] Seeding/Updating 8 Demo Students and Demo Project...")
    try:
        session = db_manager.get_session()
        students, project = seed_8_demo_students(session=session)
        print("[+] SUCCESS: 8 Demo Student Profiles seeded successfully!")
        print("-" * 68)
        print("DEMONSTRATION SHOWCASE PROJECT:")
        print(f"  Title:            {project.title}")
        print(f"  Domain:           {project.domain}")
        print(f"  Target Team Size: {project.desired_team_size} members")
        print(f"  Expected Teams:   {len(students) // project.desired_team_size} teams ({len(students)} eligible students)")
        print()
        print("DEMONSTRATION STUDENT CREDENTIALS (PASSWORD: Student@123):")
        for s in students:
            u = s.user
            print(f"  - {u.email:<28} | ID: {s.student_id:<13} | Name: {u.full_name:<22} | Dept: {s.department}")
        print("-" * 68)
    except Exception as e:
        print(f"[!] Error seeding demo students: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
