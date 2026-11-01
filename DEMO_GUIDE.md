# AI Group Project Team Builder — Evaluator Demonstration Guide

Welcome to the **AI Group Project Team Builder** demonstration environment. This guide provides evaluators and reviewers with credentials, sample workflows, and key features to test.

---

## 1. Demonstration Account Credentials

All demonstration accounts are pre-seeded in the database with secure password hashes (`scrypt` / `pbkdf2:sha256`). No plaintext passwords are stored.

### A. Faculty Lead & Administrator Account
Use this account to create and manage academic projects, generate teams using both algorithms, customize weights, and compare recommendations side-by-side.

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Faculty Lead** | `faculty@college.edu` | `Faculty@123` | Full Faculty & Project Management Dashboard |
| **Faculty Admin** | `admin@college.edu` | `Admin@123` | Administrative Faculty Access |

---

### B. Student Demonstration Accounts (16 Dedicated Profiles)
Use any of these 16 realistic student accounts to test student login, skill inventory management, profile updates, and team assignments.

| Student Account | Full Name | Academic Dept | Primary Specialization | Password |
| :--- | :--- | :--- | :--- | :--- |
| `student1@college.edu` | Alex Chen | Computer Science | Python, Backend Development, SQL, Cloud | `Student@123` |
| `student2@college.edu` | Priya Patel | Artificial Intelligence | Machine Learning, Data Science, Python, Scikit-learn | `Student@123` |
| `student3@college.edu` | Marcus Brooks | Software Engineering | React, JavaScript, HTML/CSS, UI/UX | `Student@123` |
| `student4@college.edu` | Elena Rostova | Design & Computing | UI/UX Design, HTML/CSS, Figma, Frontend | `Student@123` |
| `student5@college.edu` | Vikram Sharma | Information Technology | Java, Backend Development, SQL, Cloud | `Student@123` |
| `student6@college.edu` | Aisha Khan | Data Science | Data Analytics, SQL, Python, Pandas | `Student@123` |
| `student7@college.edu` | Lucas Silva | Computer Science | React, JavaScript, HTML/CSS, Vue.js | `Student@123` |
| `student8@college.edu` | Sophia Martinez | Software Engineering | QA / Automated Testing, Python, Java, Linux | `Student@123` |
| `student9@college.edu` | Devon Taylor | Information Technology | Cloud Computing, Docker, Linux, AWS | `Student@123` |
| `student10@college.edu`| Zack Williams | Human-Centered Computing | Project Coordination, UI/UX, Agile, Planning | `Student@123` |
| `student11@college.edu`| Ananya Deshmukh | Artificial Intelligence | Machine Learning, Scikit-learn, Data Science | `Student@123` |
| `student12@college.edu`| Daniel Kim | Computer Science | Fullstack (React + Backend Development) | `Student@123` |
| `student13@college.edu`| Olivia Brown | Design & Computing | UI/UX Design, HTML/CSS, Prototyping | `Student@123` |
| `student14@college.edu`| Arjun Nair | Data Science | Data Analytics, Cloud Computing, Python, SQL | `Student@123` |
| `student15@college.edu`| Hannah Schmidt | Software Engineering | Frontend Development, HTML/CSS, React | `Student@123` |
| `student16@college.edu`| Kevin Tan | Computer Science | Java, Backend Architecture, Multithreading | `Student@123` |

---

## 2. Pre-Seeded Academic Projects for Testing

Three dedicated demonstration projects have been configured with different skill constraints and role requirements:

### 1. AI Tutor Platform: Personalized Adaptive Learning
- **Domain**: Machine Learning & Data Science
- **Target Team Size**: 4 members (Min: 3, Max: 5)
- **Mandatory Skills**: Machine Learning (L3), Python (L3), React (L3)
- **Desired Roles**: Data & ML Engineer, Backend Developer, Frontend Developer, Project Coordinator & Researcher

### 2. Web Application Development: Enterprise Collaborative Workspace
- **Domain**: Web Application Development
- **Target Team Size**: 4 members (Min: 3, Max: 5)
- **Mandatory Skills**: React (L3), Backend Development (L3), JavaScript (L3), HTML/CSS (L3)
- **Desired Roles**: Frontend Developer, Backend Developer, UI/UX Designer, QA / Testing Engineer

### 3. Data Analytics Dashboard: Real-Time Operational Telemetry
- **Domain**: Cloud Native & Distributed Systems
- **Target Team Size**: 4 members (Min: 3, Max: 4)
- **Mandatory Skills**: Data Analytics (L3), SQL (L3), Python (L3)
- **Desired Roles**: Data & ML Engineer, Backend Developer, UI/UX Designer, Project Coordinator & Researcher

---

## 3. Step-by-Step Evaluator Walkthrough

### Test Workflow A: Student Skill Selection & Profile Verification
1. Open the application: `http://localhost:5000` (or your deployed Render URL).
2. Sign in as `student1@college.edu` with password `Student@123`.
3. Click **"Update Skill Profile"** or navigate to `/student/profile`.
4. Test the interactive Skill Selector:
   - Select a new skill (e.g., `Machine Learning`) from the dropdown.
   - Choose a proficiency level (e.g., `Level 4 - Strong`).
   - Click **Add Skill**.
   - Observe the skill immediately appearing in the active list with its category badge.
   - Adjust the proficiency inline or click the trash button to remove a skill.
   - Try adding a skill that already exists; observe that it safely updates the proficiency without creating duplicates.
5. Click **"Save Profile & Verify Completeness"**.
6. Refresh the page to confirm that all selected skills persist across reloads.
7. Click **Sign Out** from the user dropdown.

### Test Workflow B: Faculty Team Generation & Algorithm Comparison
1. Sign in as `faculty@college.edu` with password `Faculty@123`.
2. From the Faculty Dashboard, select **"AI Tutor Platform"** and click **"Generate Teams"**.
3. Inspect the **Eligible Cohort Summary**:
   - Both algorithms will operate on the exact same pool of eligible students.
   - Notice that excluded students clearly display the specific missing items (e.g. no skills or no availability schedule).
4. **Run Approach A (Rule-Based Baseline)**:
   - Adjust the criteria weights using the sliders (Skill Match, Interest, Experience, Availability, Preferred Role).
   - Click **"Generate Baseline Teams"**.
   - Review the formed teams, assigned roles, and transparent matching score breakdown.
5. Navigate back and **Run Approach B (AI/ML Recommendation)**:
   - Select the number of learned archetypes ($K=4$ clusters).
   - Click **"Fit K-Means & Recommend Teams"**.
   - Observe how Scikit-learn K-Means groups students by feature archetypes and distributes complementary skills across teams.
6. Click **"Comparison Dashboard"** to view side-by-side metrics:
   - Skill Coverage Ratio
   - Average Skill Alignment
   - Availability Compatibility
   - Multi-dimensional Radar Chart comparing both approaches.
7. Click **"Export CSV"** to download the team assignment reports.

---

## 4. Re-Seeding Data Anytime
To re-seed or verify demonstration accounts without touching existing tables:
```bash
python scripts/seed_demo.py
```
This script is non-destructive and idempotent. It will never delete or overwrite existing user accounts.
