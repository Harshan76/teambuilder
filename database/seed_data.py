"""
Synthetic Demo Data Seeder for AI Group Project Team Builder.
All data created here is purely synthetic demonstration data for academic evaluation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import db_manager, get_db
from models.entities import (
    User, StudentProfile, Skill, StudentSkill,
    Interest, StudentInterest, AvailabilitySlot, StudentAvailability,
    Role, StudentPreferredRole, Project, ProjectRequiredSkill,
    ProjectRequiredRole
)

SKILLS_DATA = [
    # Frontend
    {"name": "JavaScript", "category": "Frontend"},
    {"name": "React", "category": "Frontend"},
    {"name": "HTML/CSS", "category": "Frontend"},
    {"name": "Vue.js", "category": "Frontend"},
    {"name": "TypeScript", "category": "Frontend"},
    # Backend
    {"name": "Python", "category": "Backend"},
    {"name": "Node.js", "category": "Backend"},
    {"name": "Java", "category": "Backend"},
    {"name": "Flask", "category": "Backend"},
    {"name": "Django", "category": "Backend"},
    # Data & AI
    {"name": "Scikit-learn", "category": "Data/AI"},
    {"name": "Pandas", "category": "Data/AI"},
    {"name": "PyTorch", "category": "Data/AI"},
    {"name": "SQL", "category": "Data/AI"},
    {"name": "TensorFlow", "category": "Data/AI"},
    # DevOps & Infrastructure
    {"name": "Docker", "category": "DevOps"},
    {"name": "Git/GitHub", "category": "DevOps"},
    {"name": "Linux", "category": "DevOps"},
    {"name": "AWS", "category": "DevOps"},
    # Design & Mobile
    {"name": "Figma/UI Design", "category": "Design/Mobile"},
    {"name": "Flutter", "category": "Design/Mobile"},
]

INTERESTS_DATA = [
    {"name": "Web Application Development", "description": "Fullstack web architectures, responsive interfaces, and modern microservices"},
    {"name": "Machine Learning & Data Science", "description": "Predictive modeling, cluster discovery, and statistical learning pipelines"},
    {"name": "Cloud Native & Distributed Systems", "description": "Containerization, cloud infrastructure, and distributed microservices"},
    {"name": "Healthcare & BioInformatics", "description": "Health informatics, hospital analytics, and diagnostic decision support"},
    {"name": "FinTech & Blockchain", "description": "Financial software, fraud detection algorithms, and decentralized ledgers"},
    {"name": "Internet of Things (IoT)", "description": "Sensor telemetry, embedded devices, and smart hardware integration"},
    {"name": "Cybersecurity & Privacy", "description": "Secure coding practices, encryption, and threat vulnerability management"}
]

SLOTS_DATA = [
    {"slot_name": "Weekday Mornings", "time_range": "Mon-Fri 08:00 - 12:00"},
    {"slot_name": "Weekday Afternoons", "time_range": "Mon-Fri 12:00 - 17:00"},
    {"slot_name": "Weekday Evenings", "time_range": "Mon-Fri 17:00 - 21:00"},
    {"slot_name": "Weekend Mornings", "time_range": "Sat-Sun 09:00 - 13:00"},
    {"slot_name": "Weekend Afternoons", "time_range": "Sat-Sun 13:00 - 18:00"},
    {"slot_name": "Flexible / Anytime", "time_range": "Adaptable schedule upon team sync"}
]

ROLES_DATA = [
    {
        "name": "Frontend Developer",
        "description": "Designs and develops user interfaces, client-side interactions, and visual accessibility.",
        "key_skills_summary": "React, JavaScript, HTML/CSS, UI design"
    },
    {
        "name": "Backend Developer",
        "description": "Architects database models, API endpoints, server performance, and business logic.",
        "key_skills_summary": "Python, Node.js, Flask, Django, SQL"
    },
    {
        "name": "Data & ML Engineer",
        "description": "Builds data preparation pipelines, machine learning models, statistical analysis, and evaluations.",
        "key_skills_summary": "Scikit-learn, Pandas, Python, SQL, PyTorch"
    },
    {
        "name": "QA / Testing Engineer",
        "description": "Develops unit, integration, and user-acceptance test suites, ensuring validation and code reliability.",
        "key_skills_summary": "Git/GitHub, Python, Linux, Automated Testing"
    },
    {
        "name": "UI/UX Designer",
        "description": "Creates wireframes, design systems, user personas, and conducts usability testing.",
        "key_skills_summary": "Figma/UI Design, HTML/CSS, Prototyping"
    },
    {
        "name": "Project Coordinator & Researcher",
        "description": "Organizes milestones, manages team deliverables, leads documentation, and literature review.",
        "key_skills_summary": "Git/GitHub, Technical Writing, Planning"
    }
]

# 24 Synthetic Students with realistic, rich portfolios
STUDENTS_DATA = [
    # 1 - 4: Strong Backend Specialists
    {
        "email": "alex.chen@college.edu", "full_name": "Alex Chen", "student_id": "STU2026-001", "department": "Computer Science",
        "experience_level": "Advanced", "experience_years": 3.0,
        "previous_projects": "Architected an asynchronous event-driven REST API handling 2,500 req/sec using Python, Flask, Redis, and MySQL. Implemented JWT authentication and Docker containerization.",
        "skills": {"Python": 5, "Flask": 5, "SQL": 4, "Docker": 4, "Git/GitHub": 4},
        "interests": ["Web Application Development", "Cloud Native & Distributed Systems"],
        "availability": ["Weekday Evenings", "Weekend Mornings", "Flexible / Anytime"],
        "roles": [("Backend Developer", 1), ("QA / Testing Engineer", 2)]
    },
    {
        "email": "fatima.zahra@college.edu", "full_name": "Fatima Zahra", "student_id": "STU2026-002", "department": "Software Engineering",
        "experience_level": "Advanced", "experience_years": 2.5,
        "previous_projects": "Engineered multi-tenant financial accounting microservices using Django and PostgreSQL. Built automated reconciliation batch jobs and cryptographic checksum audit logging.",
        "skills": {"Python": 5, "Django": 4, "SQL": 5, "Linux": 4, "Git/GitHub": 4},
        "interests": ["FinTech & Blockchain", "Web Application Development"],
        "availability": ["Weekday Evenings", "Weekend Afternoons"],
        "roles": [("Backend Developer", 1), ("Project Coordinator & Researcher", 2)]
    },
    {
        "email": "marcus.brooks@college.edu", "full_name": "Marcus Brooks", "student_id": "STU2026-003", "department": "Computer Science",
        "experience_level": "Intermediate", "experience_years": 1.5,
        "previous_projects": "Developed a real-time collaborative document server using Node.js, Express, and WebSocket protocols. Built relational schema migrations with Knex.js and MySQL.",
        "skills": {"Node.js": 4, "JavaScript": 4, "SQL": 3, "Docker": 2, "Git/GitHub": 3},
        "interests": ["Web Application Development", "Cloud Native & Distributed Systems"],
        "availability": ["Weekday Mornings", "Weekday Evenings"],
        "roles": [("Backend Developer", 1), ("Frontend Developer", 2)]
    },
    {
        "email": "vikram.sharma@college.edu", "full_name": "Vikram Sharma", "student_id": "STU2026-004", "department": "Information Technology",
        "experience_level": "Intermediate", "experience_years": 2.0,
        "previous_projects": "Created a hospital equipment tracking service using Java Spring Boot and Flask. Integrated role-based access control and encrypted MySQL database connections.",
        "skills": {"Python": 4, "Java": 4, "SQL": 4, "Linux": 3, "Git/GitHub": 3},
        "interests": ["Cloud Native & Distributed Systems", "Cybersecurity & Privacy"],
        "availability": ["Weekday Evenings", "Weekend Mornings"],
        "roles": [("Backend Developer", 1), ("QA / Testing Engineer", 2)]
    },

    # 5 - 8: Frontend & UI/UX Specialists
    {
        "email": "elena.rostova@college.edu", "full_name": "Elena Rostova", "student_id": "STU2026-005", "department": "Computer Science",
        "experience_level": "Advanced", "experience_years": 2.5,
        "previous_projects": "Designed and built an interactive clinical monitoring dashboard in React 18 and TypeScript with Chart.js. Achieved 98% Lighthouse accessibility and sub-1s load times.",
        "skills": {"React": 5, "JavaScript": 5, "HTML/CSS": 5, "TypeScript": 4, "Figma/UI Design": 4},
        "interests": ["Web Application Development", "Healthcare & BioInformatics"],
        "availability": ["Weekday Evenings", "Weekend Mornings", "Flexible / Anytime"],
        "roles": [("Frontend Developer", 1), ("UI/UX Designer", 2)]
    },
    {
        "email": "devon.taylor@college.edu", "full_name": "Devon Taylor", "student_id": "STU2026-006", "department": "Human-Centered Computing",
        "experience_level": "Intermediate", "experience_years": 2.0,
        "previous_projects": "Created a design token system and 40+ responsive UI components in Figma and React. Conducted cognitive walkthroughs and usability testing with 30 target users.",
        "skills": {"Figma/UI Design": 5, "HTML/CSS": 5, "React": 4, "JavaScript": 3},
        "interests": ["Web Application Development", "Healthcare & BioInformatics"],
        "availability": ["Weekday Afternoons", "Weekday Evenings", "Weekend Mornings"],
        "roles": [("UI/UX Designer", 1), ("Frontend Developer", 2)]
    },
    {
        "email": "aisha.patel@college.edu", "full_name": "Aisha Patel", "student_id": "STU2026-007", "department": "Software Engineering",
        "experience_level": "Intermediate", "experience_years": 1.5,
        "previous_projects": "Built responsive e-commerce web applications using Vue 3 and React. Integrated Tailwind CSS and Pinia state management for cross-device mobile shopping flows.",
        "skills": {"JavaScript": 4, "Vue.js": 4, "HTML/CSS": 4, "React": 3, "Git/GitHub": 3},
        "interests": ["Web Application Development", "FinTech & Blockchain"],
        "availability": ["Weekday Mornings", "Weekday Evenings"],
        "roles": [("Frontend Developer", 1), ("UI/UX Designer", 2)]
    },
    {
        "email": "lucas.silva@college.edu", "full_name": "Lucas Silva", "student_id": "STU2026-008", "department": "Computer Science",
        "experience_level": "Intermediate", "experience_years": 2.0,
        "previous_projects": "Engineered single-page applications with React and Next.js. Integrated Framer Motion micro-interactions, responsive data grids, and GitHub Actions CI pipelines.",
        "skills": {"React": 4, "JavaScript": 4, "HTML/CSS": 4, "TypeScript": 3, "Git/GitHub": 4},
        "interests": ["Web Application Development", "FinTech & Blockchain"],
        "availability": ["Weekday Evenings", "Weekend Mornings", "Weekend Afternoons"],
        "roles": [("Frontend Developer", 1), ("Project Coordinator & Researcher", 2)]
    },

    # 9 - 12: Data & Machine Learning Specialists
    {
        "email": "drishya.nair@college.edu", "full_name": "Drishya Nair", "student_id": "STU2026-009", "department": "Data Science",
        "experience_level": "Advanced", "experience_years": 3.0,
        "previous_projects": "Trained and validated disease risk classification and patient clustering pipelines with Scikit-learn and Pandas. Achieved 0.91 ROC-AUC on MIMIC-III clinical datasets.",
        "skills": {"Scikit-learn": 5, "Pandas": 5, "Python": 5, "SQL": 4, "PyTorch": 3},
        "interests": ["Machine Learning & Data Science", "Healthcare & BioInformatics"],
        "availability": ["Weekday Evenings", "Weekend Mornings", "Flexible / Anytime"],
        "roles": [("Data & ML Engineer", 1), ("Project Coordinator & Researcher", 2)]
    },
    {
        "email": "kevin.o-connor@college.edu", "full_name": "Kevin O'Connor", "student_id": "STU2026-010", "department": "Computer Science",
        "experience_level": "Intermediate", "experience_years": 2.0,
        "previous_projects": "Conducted automated feature selection and hyperparameter optimization for churn prediction pipelines using Pandas and Scikit-learn RandomizedSearchCV.",
        "skills": {"Python": 4, "Pandas": 4, "Scikit-learn": 4, "SQL": 3, "Git/GitHub": 3},
        "interests": ["Machine Learning & Data Science", "Healthcare & BioInformatics"],
        "availability": ["Weekday Evenings", "Weekend Afternoons"],
        "roles": [("Data & ML Engineer", 1), ("QA / Testing Engineer", 2)]
    },
    {
        "email": "mei.ling@college.edu", "full_name": "Mei Ling", "student_id": "STU2026-011", "department": "Artificial Intelligence",
        "experience_level": "Advanced", "experience_years": 2.5,
        "previous_projects": "Developed PyTorch and Scikit-learn unsupervised feature extraction models for sensor anomaly detection in smart IoT grids with 94% precision.",
        "skills": {"Python": 5, "Scikit-learn": 5, "PyTorch": 4, "Pandas": 5, "TensorFlow": 3},
        "interests": ["Machine Learning & Data Science", "Internet of Things (IoT)"],
        "availability": ["Weekday Mornings", "Weekday Evenings", "Weekend Mornings"],
        "roles": [("Data & ML Engineer", 1), ("Project Coordinator & Researcher", 2)]
    },
    {
        "email": "samir.khan@college.edu", "full_name": "Samir Khan", "student_id": "STU2026-012", "department": "Data Science",
        "experience_level": "Intermediate", "experience_years": 1.5,
        "previous_projects": "Built an automated ETL data warehousing pipeline aggregating 100K+ daily financial ledger records using Python, Pandas, and MySQL indexing.",
        "skills": {"Python": 4, "Pandas": 4, "SQL": 4, "Scikit-learn": 3, "Git/GitHub": 3},
        "interests": ["Machine Learning & Data Science", "FinTech & Blockchain"],
        "availability": ["Weekday Evenings", "Weekend Mornings"],
        "roles": [("Data & ML Engineer", 1), ("Backend Developer", 2)]
    },

    # 13 - 16: Fullstack & Generalists
    {
        "email": "jordan.miller@college.edu", "full_name": "Jordan Miller", "student_id": "STU2026-013", "department": "Software Engineering",
        "experience_level": "Advanced", "experience_years": 3.0,
        "previous_projects": "Delivered end-to-end fullstack applications featuring a React Single Page frontend, Flask REST APIs, PostgreSQL, and Docker Compose development environments.",
        "skills": {"Python": 4, "Flask": 4, "React": 4, "JavaScript": 4, "SQL": 3, "Git/GitHub": 4},
        "interests": ["Web Application Development", "Cloud Native & Distributed Systems"],
        "availability": ["Weekday Evenings", "Weekend Mornings", "Flexible / Anytime"],
        "roles": [("Frontend Developer", 1), ("Backend Developer", 2)]
    },
    {
        "email": "ananya.rao@college.edu", "full_name": "Ananya Rao", "student_id": "STU2026-014", "department": "Computer Science",
        "experience_level": "Intermediate", "experience_years": 2.0,
        "previous_projects": "Engineered real-time data visualizers connecting React and Chart.js to a Flask streaming telemetry backend for environmental monitoring.",
        "skills": {"Python": 4, "React": 3, "Pandas": 3, "JavaScript": 3, "HTML/CSS": 4, "Git/GitHub": 3},
        "interests": ["Web Application Development", "Machine Learning & Data Science"],
        "availability": ["Weekday Evenings", "Weekend Mornings"],
        "roles": [("Frontend Developer", 1), ("Data & ML Engineer", 2)]
    },
    {
        "email": "carlos.mendoza@college.edu", "full_name": "Carlos Mendoza", "student_id": "STU2026-015", "department": "Computer Science",
        "experience_level": "Intermediate", "experience_years": 2.0,
        "previous_projects": "Containerized multi-tier web applications using Docker, Gunicorn, and Django. Configured Nginx reverse proxies with SSL termination.",
        "skills": {"Python": 4, "Django": 3, "Docker": 3, "JavaScript": 3, "SQL": 3, "Git/GitHub": 4},
        "interests": ["Cloud Native & Distributed Systems", "Web Application Development"],
        "availability": ["Weekday Mornings", "Weekday Evenings", "Weekend Afternoons"],
        "roles": [("Backend Developer", 1), ("QA / Testing Engineer", 2)]
    },
    {
        "email": "sophia.hansen@college.edu", "full_name": "Sophia Hansen", "student_id": "STU2026-016", "department": "Software Engineering",
        "experience_level": "Intermediate", "experience_years": 1.5,
        "previous_projects": "Managed sprint deliverables for a 5-student academic project, authoring system architecture diagrams and automated REST API integration tests with Pytest.",
        "skills": {"Python": 3, "JavaScript": 3, "HTML/CSS": 4, "Flask": 3, "Git/GitHub": 4},
        "interests": ["Web Application Development", "Healthcare & BioInformatics"],
        "availability": ["Weekday Evenings", "Weekend Mornings"],
        "roles": [("Project Coordinator & Researcher", 1), ("Frontend Developer", 2)]
    },

    # 17 - 20: QA, DevOps & Infrastructure
    {
        "email": "tariq.al-mansoor@college.edu", "full_name": "Tariq Al-Mansoor", "student_id": "STU2026-017", "department": "Information Technology",
        "experience_level": "Advanced", "experience_years": 2.5,
        "previous_projects": "Built robust GitHub Actions CI/CD pipelines deploying Docker containers to AWS ECS. Enforced 85%+ test coverage standards using Pytest and SonarQube.",
        "skills": {"Docker": 5, "Linux": 4, "Git/GitHub": 5, "Python": 4, "SQL": 3},
        "interests": ["Cloud Native & Distributed Systems", "Cybersecurity & Privacy"],
        "availability": ["Weekday Evenings", "Weekend Mornings", "Flexible / Anytime"],
        "roles": [("QA / Testing Engineer", 1), ("Backend Developer", 2)]
    },
    {
        "email": "claire.dubois@college.edu", "full_name": "Claire Dubois", "student_id": "STU2026-018", "department": "Software Engineering",
        "experience_level": "Intermediate", "experience_years": 2.0,
        "previous_projects": "Authored comprehensive end-to-end integration and smoke test suites for academic web platforms. Documented bug triage workflows in GitHub Projects.",
        "skills": {"Python": 3, "Git/GitHub": 4, "Linux": 3, "SQL": 3, "HTML/CSS": 3},
        "interests": ["Healthcare & BioInformatics", "Web Application Development"],
        "availability": ["Weekday Afternoons", "Weekday Evenings"],
        "roles": [("QA / Testing Engineer", 1), ("Project Coordinator & Researcher", 2)]
    },
    {
        "email": "rahul.deshmukh@college.edu", "full_name": "Rahul Deshmukh", "student_id": "STU2026-019", "department": "Computer Science",
        "experience_level": "Intermediate", "experience_years": 1.5,
        "previous_projects": "Configured Ubuntu Linux production servers, systemd service daemonization, firewall policies, and automated shell backup cron jobs.",
        "skills": {"Linux": 4, "Docker": 3, "Python": 3, "Git/GitHub": 4, "SQL": 2},
        "interests": ["Internet of Things (IoT)", "Cloud Native & Distributed Systems"],
        "availability": ["Weekday Evenings", "Weekend Mornings"],
        "roles": [("QA / Testing Engineer", 1), ("Backend Developer", 2)]
    },
    {
        "email": "zoe.kravitz@college.edu", "full_name": "Zoe Kravitz", "student_id": "STU2026-020", "department": "Computer Science",
        "experience_level": "Intermediate", "experience_years": 2.0,
        "previous_projects": "Coordinated academic project deliverables, technical IEEE documentation, Jira user stories, and acceptance criteria verification with faculty sponsors.",
        "skills": {"Git/GitHub": 4, "Python": 3, "HTML/CSS": 3, "SQL": 3, "Figma/UI Design": 3},
        "interests": ["Healthcare & BioInformatics", "Web Application Development"],
        "availability": ["Weekday Mornings", "Weekday Evenings", "Flexible / Anytime"],
        "roles": [("Project Coordinator & Researcher", 1), ("UI/UX Designer", 2)]
    },

    # 21 - 24: Emerging / Junior & Diverse Learners
    {
        "email": "liam.wright@college.edu", "full_name": "Liam Wright", "student_id": "STU2026-021", "department": "Computer Science",
        "experience_level": "Beginner", "experience_years": 1.0,
        "previous_projects": "Built responsive personal portfolio websites and beginner Python automation scripts for data cleanup. Eager to master frontend frameworks and testing.",
        "skills": {"HTML/CSS": 3, "JavaScript": 2, "Python": 2, "Git/GitHub": 2},
        "interests": ["Web Application Development", "Internet of Things (IoT)"],
        "availability": ["Weekday Evenings", "Weekend Mornings"],
        "roles": [("Frontend Developer", 1), ("QA / Testing Engineer", 2)]
    },
    {
        "email": "priya.sen@college.edu", "full_name": "Priya Sen", "student_id": "STU2026-022", "department": "Data Science",
        "experience_level": "Intermediate", "experience_years": 1.5,
        "previous_projects": "Conducted statistical exploratory data analysis and visual reports on environmental sensor logs using Python, Pandas, and Matplotlib.",
        "skills": {"Python": 3, "Pandas": 4, "Scikit-learn": 3, "SQL": 3},
        "interests": ["Internet of Things (IoT)", "Machine Learning & Data Science"],
        "availability": ["Weekday Evenings", "Weekend Mornings"],
        "roles": [("Data & ML Engineer", 1), ("Project Coordinator & Researcher", 2)]
    },
    {
        "email": "noah.kim@college.edu", "full_name": "Noah Kim", "student_id": "STU2026-023", "department": "Information Systems",
        "experience_level": "Intermediate", "experience_years": 1.5,
        "previous_projects": "Researched Agile scrum team coordination and authored technical specifications for database entity relationships and REST API contracts.",
        "skills": {"Git/GitHub": 4, "Python": 3, "SQL": 3, "HTML/CSS": 2},
        "interests": ["FinTech & Blockchain", "Web Application Development"],
        "availability": ["Weekday Evenings", "Weekend Afternoons", "Flexible / Anytime"],
        "roles": [("Project Coordinator & Researcher", 1), ("Backend Developer", 2)]
    },
    {
        "email": "chloe.dupont@college.edu", "full_name": "Chloe Dupont", "student_id": "STU2026-024", "department": "Design & Computing",
        "experience_level": "Intermediate", "experience_years": 1.5,
        "previous_projects": "Designed accessible web interfaces and component libraries in Figma following WCAG 2.1 AA contrast and typography guidelines.",
        "skills": {"Figma/UI Design": 4, "HTML/CSS": 4, "JavaScript": 2, "Git/GitHub": 2},
        "interests": ["Healthcare & BioInformatics", "Web Application Development"],
        "availability": ["Weekday Evenings", "Weekend Mornings"],
        "roles": [("UI/UX Designer", 1), ("Frontend Developer", 2)]
    }
]

PROJECTS_DATA = [
    {
        "title": "Intelligent HealthCare Analytics Portal",
        "domain": "Healthcare & BioInformatics",
        "description": "Architect a cloud-native healthcare platform integrating real-time telemetry from patient monitors, predictive risk stratification models (cardiovascular & diabetes risk scoring via Scikit-learn), HIPAA-compliant audit trails, and an accessible React provider dashboard.",
        "desired_team_size": 4,
        "min_team_size": 3,
        "max_team_size": 5,
        "experience_level_required": "Intermediate",
        "status": "Open",
        "required_skills": [
            {"skill_name": "Python", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.2},
            {"skill_name": "React", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.1},
            {"skill_name": "Scikit-learn", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.2},
            {"skill_name": "SQL", "min_proficiency": 2, "is_mandatory": False, "priority_weight": 1.0}
        ],
        "required_roles": [
            {"role_name": "Backend Developer", "count": 1},
            {"role_name": "Frontend Developer", "count": 1},
            {"role_name": "Data & ML Engineer", "count": 1},
            {"role_name": "Project Coordinator & Researcher", "count": 1}
        ]
    },
    {
        "title": "Smart Campus IoT Energy Optimization",
        "domain": "Internet of Things (IoT)",
        "description": "Build an IoT monitoring backend and analytics pipeline that collects real-time sensor metrics from smart classrooms, optimizes heating/lighting consumption, and alerts campus facilities.",
        "desired_team_size": 4,
        "min_team_size": 3,
        "max_team_size": 4,
        "experience_level_required": "Intermediate",
        "status": "Open",
        "required_skills": [
            {"skill_name": "Python", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.1},
            {"skill_name": "Docker", "min_proficiency": 2, "is_mandatory": True, "priority_weight": 1.0},
            {"skill_name": "Pandas", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.0},
            {"skill_name": "Linux", "min_proficiency": 2, "is_mandatory": False, "priority_weight": 0.9}
        ],
        "required_roles": [
            {"role_name": "Backend Developer", "count": 1},
            {"role_name": "Data & ML Engineer", "count": 1},
            {"role_name": "QA / Testing Engineer", "count": 1},
            {"role_name": "Project Coordinator & Researcher", "count": 1}
        ]
    },
    {
        "title": "Decentralized Micro-Finance & Escrow App",
        "domain": "FinTech & Blockchain",
        "description": "Create an automated, transparent micro-loan management application with peer validation, audit trails, and intuitive borrower loan application tracking.",
        "desired_team_size": 3,
        "min_team_size": 3,
        "max_team_size": 4,
        "experience_level_required": "Intermediate",
        "status": "Open",
        "required_skills": [
            {"skill_name": "Node.js", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.1},
            {"skill_name": "React", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.1},
            {"skill_name": "Git/GitHub", "min_proficiency": 2, "is_mandatory": False, "priority_weight": 1.0}
        ],
        "required_roles": [
            {"role_name": "Frontend Developer", "count": 1},
            {"role_name": "Backend Developer", "count": 1},
            {"role_name": "QA / Testing Engineer", "count": 1}
        ]
    },
    {
        "title": "CloudSentinel: Zero-Trust Threat Intelligence Platform",
        "domain": "Cybersecurity & Privacy",
        "description": "Engineer a DevSecOps orchestration engine providing automated container vulnerability scanning, real-time access drift detection, cryptographically signed audit logs, and security posture monitoring dashboards.",
        "desired_team_size": 4,
        "min_team_size": 3,
        "max_team_size": 4,
        "experience_level_required": "Intermediate",
        "status": "Open",
        "required_skills": [
            {"skill_name": "Docker", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.2},
            {"skill_name": "Linux", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.1},
            {"skill_name": "Python", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.1},
            {"skill_name": "Git/GitHub", "min_proficiency": 3, "is_mandatory": False, "priority_weight": 1.0}
        ],
        "required_roles": [
            {"role_name": "Backend Developer", "count": 1},
            {"role_name": "QA / Testing Engineer", "count": 1},
            {"role_name": "Project Coordinator & Researcher", "count": 1},
            {"role_name": "Frontend Developer", "count": 1}
        ]
    },
    {
        "title": "HyperShop: Omnichannel E-Commerce & Recommendation Engine",
        "domain": "Web Application Development",
        "description": "Construct a high-performance headless retail platform featuring sub-100ms catalog search, personalized customer recommendations via machine learning, and an accessible mobile-responsive UI design system.",
        "desired_team_size": 4,
        "min_team_size": 3,
        "max_team_size": 5,
        "experience_level_required": "Intermediate",
        "status": "Open",
        "required_skills": [
            {"skill_name": "React", "min_proficiency": 4, "is_mandatory": True, "priority_weight": 1.2},
            {"skill_name": "JavaScript", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.0},
            {"skill_name": "Python", "min_proficiency": 3, "is_mandatory": True, "priority_weight": 1.1},
            {"skill_name": "Figma/UI Design", "min_proficiency": 3, "is_mandatory": False, "priority_weight": 1.0}
        ],
        "required_roles": [
            {"role_name": "Frontend Developer", "count": 1},
            {"role_name": "Backend Developer", "count": 1},
            {"role_name": "UI/UX Designer", "count": 1},
            {"role_name": "Data & ML Engineer", "count": 1}
        ]
    }
]

def seed_database(session=None):
    """Populates or updates the database with catalogs, faculty accounts, synthetic student profiles, and demo projects."""
    db = session or get_db()
    
    # 1. Seed Skills
    skill_map = {}
    for item in SKILLS_DATA:
        s = db.query(Skill).filter_by(name=item["name"]).first()
        if not s:
            s = Skill(name=item["name"], category=item["category"])
            db.add(s)
            db.flush()
        else:
            s.category = item["category"]
        skill_map[s.name] = s

    # 2. Seed Interests
    interest_map = {}
    for item in INTERESTS_DATA:
        i = db.query(Interest).filter_by(name=item["name"]).first()
        if not i:
            i = Interest(name=item["name"], description=item["description"])
            db.add(i)
            db.flush()
        else:
            i.description = item["description"]
        interest_map[i.name] = i

    # 3. Seed Availability Slots
    slot_map = {}
    for item in SLOTS_DATA:
        slot = db.query(AvailabilitySlot).filter_by(slot_name=item["slot_name"]).first()
        if not slot:
            slot = AvailabilitySlot(slot_name=item["slot_name"], time_range=item["time_range"])
            db.add(slot)
            db.flush()
        else:
            slot.time_range = item["time_range"]
        slot_map[slot.slot_name] = slot

    # 4. Seed Roles
    role_map = {}
    for item in ROLES_DATA:
        r = db.query(Role).filter_by(name=item["name"]).first()
        if not r:
            r = Role(name=item["name"], description=item["description"], key_skills_summary=item["key_skills_summary"])
            db.add(r)
            db.flush()
        else:
            r.description = item["description"]
            r.key_skills_summary = item["key_skills_summary"]
        role_map[r.name] = r

    # 5. Seed Faculty Users
    faculty_user = db.query(User).filter_by(email="faculty@college.edu").first()
    if not faculty_user:
        faculty_user = User(
            email="faculty@college.edu",
            full_name="Dr. Sarah Mitchell",
            role="faculty"
        )
        faculty_user.set_password("Faculty@123")
        db.add(faculty_user)
        db.flush()

    admin_faculty = db.query(User).filter_by(email="admin@college.edu").first()
    if not admin_faculty:
        admin_faculty = User(
            email="admin@college.edu",
            full_name="Prof. Alan Vance",
            role="faculty"
        )
        admin_faculty.set_password("Admin@123")
        db.add(admin_faculty)
        db.flush()

    # 6. Seed Synthetic Students
    for s_data in STUDENTS_DATA:
        u = db.query(User).filter_by(email=s_data["email"]).first()
        if not u:
            u = User(
                email=s_data["email"],
                full_name=s_data["full_name"],
                role="student"
            )
            u.set_password("Student@123")
            db.add(u)
            db.flush()

            profile = StudentProfile(
                user_id=u.id,
                student_id=s_data["student_id"],
                department=s_data["department"],
                experience_level=s_data["experience_level"],
                experience_years=s_data["experience_years"],
                previous_projects_summary=s_data["previous_projects"],
                collaboration_preference="Flexible / Balanced",
                is_profile_complete=True
            )
            db.add(profile)
            db.flush()

            # Add skills
            for s_name, prof in s_data["skills"].items():
                if s_name in skill_map:
                    db.add(StudentSkill(
                        profile_id=profile.id,
                        skill_id=skill_map[s_name].id,
                        proficiency=prof
                    ))

            # Add interests
            for i_name in s_data["interests"]:
                if i_name in interest_map:
                    db.add(StudentInterest(
                        profile_id=profile.id,
                        interest_id=interest_map[i_name].id
                    ))

            # Add availability
            for slot_name in s_data["availability"]:
                if slot_name in slot_map:
                    db.add(StudentAvailability(
                        profile_id=profile.id,
                        slot_id=slot_map[slot_name].id
                    ))

            # Add preferred roles
            for r_name, rank in s_data["roles"]:
                if r_name in role_map:
                    db.add(StudentPreferredRole(
                        profile_id=profile.id,
                        role_id=role_map[r_name].id,
                        preference_rank=rank
                    ))
        else:
            # Update existing profile summary
            if u.profile:
                u.profile.previous_projects_summary = s_data["previous_projects"]
                u.profile.experience_years = s_data["experience_years"]
                u.profile.experience_level = s_data["experience_level"]
                u.profile.department = s_data["department"]
                u.profile.is_profile_complete = True

    # 7. Seed Demo Projects
    for p_data in PROJECTS_DATA:
        proj = db.query(Project).filter_by(title=p_data["title"]).first()
        if not proj:
            proj = Project(
                title=p_data["title"],
                domain=p_data["domain"],
                description=p_data["description"],
                desired_team_size=p_data["desired_team_size"],
                min_team_size=p_data["min_team_size"],
                max_team_size=p_data["max_team_size"],
                experience_level_required=p_data["experience_level_required"],
                status=p_data["status"],
                created_by=faculty_user.id
            )
            db.add(proj)
            db.flush()

            for sk in p_data["required_skills"]:
                if sk["skill_name"] in skill_map:
                    db.add(ProjectRequiredSkill(
                        project_id=proj.id,
                        skill_id=skill_map[sk["skill_name"]].id,
                        min_proficiency=sk["min_proficiency"],
                        is_mandatory=sk["is_mandatory"],
                        priority_weight=sk["priority_weight"]
                    ))

            for rl in p_data["required_roles"]:
                if rl["role_name"] in role_map:
                    db.add(ProjectRequiredRole(
                        project_id=proj.id,
                        role_id=role_map[rl["role_name"]].id,
                        count_needed=rl["count"]
                    ))
        else:
            # Update description and domain on existing projects
            proj.description = p_data["description"]
            proj.domain = p_data["domain"]
            proj.desired_team_size = p_data["desired_team_size"]
            proj.min_team_size = p_data["min_team_size"]
            proj.max_team_size = p_data["max_team_size"]

    db.commit()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    db_manager.init_db()
    db_manager.create_all()
    seed_database()
