"""
scripts/seed_demo.py
====================================================================
Dedicated Idempotent Demonstration Data Seeder for Hackathon Evaluators.
Populates Aiven MySQL / Local Database with:
- 1 Verified Faculty Lead Demonstration Account
- 16 Realistic Student Demonstration Accounts with Diverse Profiles
- 3 Academic Demonstration Projects (AI Tutor, Web App, Data Analytics)
- Dynamic Availability Slots in Asia/Kolkata (IST) Timezone
- Full Technical Skills Catalog (Python, Java, React, ML, SQL, etc.)

Database Safety Guarantee:
- Never drops existing tables.
- Never deletes or truncates existing user accounts.
- Completely idempotent: safe to execute multiple times.
====================================================================
"""

import sys
from pathlib import Path

# Add project root directory to Python module path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.db import db_manager, get_db
from database.seed_data import seed_database

def main():
    print("=" * 65)
    print("  AI GROUP PROJECT TEAM BUILDER - DEMO DATA INITIALIZATION")
    print("=" * 65)
    print("[*] Initializing database connection pool...")
    db_manager.init_db()
    print(f"[*] Connection status: {db_manager.connection_status_message}")

    print("[*] Ensuring all schema tables exist safely (non-destructive)...")
    db_manager.create_all()
    print("[+] Database schema verified.")

    print("[*] Populating demonstration catalog, accounts, and projects...")
    try:
        seed_database()
        print("[+] SUCCESS: Demonstration dataset seeded successfully!")
        print("-" * 65)
        print("DEMONSTRATION LOGIN CREDENTIALS:")
        print("  Faculty Account:")
        print("    Email:    faculty@college.edu")
        print("    Password: Faculty@123")
        print("    Role:     Faculty / Project Creator / Reviewer")
        print()
        print("  Student Accounts (16 Available):")
        print("    Emails:   student1@college.edu to student16@college.edu")
        print("    Password: Student@123")
        print("    Profiles: Complete with skills, availability, and interests.")
        print("-" * 65)
    except Exception as e:
        print(f"[!] Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
