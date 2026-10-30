"""
Database initialization and reset script.
Usage:
    py scripts/init_db.py [--reset] [--seed]
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.db import db_manager, Base
from database.seed_data import seed_database

def main():
    parser = argparse.ArgumentParser(description="Initialize AI Group Project Team Builder Database")
    parser.add_argument("--reset", action="store_true", help="Drop all existing tables before recreating")
    parser.add_argument("--seed", action="store_true", default=True, help="Seed synthetic demo data")
    args = parser.parse_args()

    print("[*] Initializing database engine...")
    db_manager.init_db()
    print(f"[*] {db_manager.connection_status_message}")

    if args.reset:
        print("[!] Dropping all existing tables...")
        Base.metadata.drop_all(db_manager.engine)
        print("[+] Tables dropped.")

    print("[*] Creating all schema tables...")
    db_manager.create_all()
    print("[+] Schema tables created.")

    if args.seed:
        print("[*] Seeding synthetic demonstration dataset...")
        seed_database()
        print("[+] Database successfully initialized and seeded with synthetic demo records!")

if __name__ == "__main__":
    main()
