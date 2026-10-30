-- =====================================================================
-- AI Group Project Team Builder - MySQL Normalized Relational Schema
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `ai_team_builder` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `ai_team_builder`;

-- 1. Users Table (Authentication & RBAC)
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(191) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('student', 'faculty') NOT NULL DEFAULT 'student',
    `full_name` VARCHAR(150) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Student Profiles
CREATE TABLE IF NOT EXISTS `student_profiles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `student_id` VARCHAR(50) NOT NULL UNIQUE,
    `department` VARCHAR(100) NOT NULL,
    `experience_level` ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL DEFAULT 'Beginner',
    `experience_years` DECIMAL(3, 1) DEFAULT 0.0,
    `previous_projects_summary` TEXT,
    `collaboration_preference` VARCHAR(100) DEFAULT 'Flexible / Balanced',
    `is_profile_complete` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_profiles_experience` (`experience_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Skills Catalog
CREATE TABLE IF NOT EXISTS `skills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `category` VARCHAR(50) NOT NULL,
    INDEX `idx_skills_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Student Skills (Proficiency levels 1-5)
CREATE TABLE IF NOT EXISTS `student_skills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `profile_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    `proficiency` INT NOT NULL CHECK (`proficiency` BETWEEN 1 AND 5),
    UNIQUE KEY `uk_student_skill` (`profile_id`, `skill_id`),
    FOREIGN KEY (`profile_id`) REFERENCES `student_profiles`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`skill_id`) REFERENCES `skills`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Interests Catalog
CREATE TABLE IF NOT EXISTS `interests` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Student Interests
CREATE TABLE IF NOT EXISTS `student_interests` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `profile_id` INT NOT NULL,
    `interest_id` INT NOT NULL,
    UNIQUE KEY `uk_student_interest` (`profile_id`, `interest_id`),
    FOREIGN KEY (`profile_id`) REFERENCES `student_profiles`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`interest_id`) REFERENCES `interests`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Availability Slots Catalog
CREATE TABLE IF NOT EXISTS `availability_slots` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `slot_name` VARCHAR(100) NOT NULL UNIQUE,
    `time_range` VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Student Availability
CREATE TABLE IF NOT EXISTS `student_availability` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `profile_id` INT NOT NULL,
    `slot_id` INT NOT NULL,
    UNIQUE KEY `uk_student_availability` (`profile_id`, `slot_id`),
    FOREIGN KEY (`profile_id`) REFERENCES `student_profiles`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`slot_id`) REFERENCES `availability_slots`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Roles Catalog
CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT,
    `key_skills_summary` VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Student Preferred Roles (Ranked preference)
CREATE TABLE IF NOT EXISTS `student_preferred_roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `profile_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    `preference_rank` INT NOT NULL DEFAULT 1,
    UNIQUE KEY `uk_student_role` (`profile_id`, `role_id`),
    FOREIGN KEY (`profile_id`) REFERENCES `student_profiles`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Projects (Managed by Faculty)
CREATE TABLE IF NOT EXISTS `projects` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `description` TEXT,
    `domain` VARCHAR(100) NOT NULL,
    `desired_team_size` INT NOT NULL DEFAULT 4,
    `min_team_size` INT NOT NULL DEFAULT 3,
    `max_team_size` INT NOT NULL DEFAULT 5,
    `experience_level_required` ENUM('Beginner', 'Intermediate', 'Advanced', 'Any') NOT NULL DEFAULT 'Any',
    `status` ENUM('Draft', 'Open', 'Formed', 'Finalized') NOT NULL DEFAULT 'Open',
    `created_by` INT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_projects_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. Project Required Skills
CREATE TABLE IF NOT EXISTS `project_required_skills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    `min_proficiency` INT NOT NULL DEFAULT 2 CHECK (`min_proficiency` BETWEEN 1 AND 5),
    `is_mandatory` BOOLEAN NOT NULL DEFAULT TRUE,
    `priority_weight` DECIMAL(3, 2) NOT NULL DEFAULT 1.0,
    UNIQUE KEY `uk_project_skill` (`project_id`, `skill_id`),
    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`skill_id`) REFERENCES `skills`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. Project Required Roles
CREATE TABLE IF NOT EXISTS `project_required_roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `role_id` INT NOT NULL,
    `count_needed` INT NOT NULL DEFAULT 1,
    UNIQUE KEY `uk_project_role` (`project_id`, `role_id`),
    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. Model Runs (Unsupervised K-Means model metadata & versioning)
CREATE TABLE IF NOT EXISTS `model_runs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `algorithm` VARCHAR(50) NOT NULL DEFAULT 'K-Means',
    `n_clusters` INT NOT NULL,
    `silhouette_score` DECIMAL(6, 4),
    `inertia` DECIMAL(12, 4),
    `n_samples` INT NOT NULL,
    `features_json` TEXT,
    `model_file_path` VARCHAR(255),
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `trained_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. Team Generation Runs (Tracks generation execution & configuration)
CREATE TABLE IF NOT EXISTS `team_generation_runs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `method` ENUM('baseline', 'ml') NOT NULL,
    `weights_json` TEXT,
    `random_seed` INT DEFAULT 42,
    `n_teams` INT NOT NULL,
    `n_students_assigned` INT NOT NULL,
    `n_students_unassigned` INT NOT NULL DEFAULT 0,
    `runtime_seconds` DECIMAL(8, 4) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 16. Teams Table
CREATE TABLE IF NOT EXISTS `teams` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `project_id` INT NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `generation_method` ENUM('baseline', 'ml', 'manual') NOT NULL,
    `run_id` INT,
    `status` ENUM('Proposed', 'Approved', 'Finalized') NOT NULL DEFAULT 'Proposed',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`run_id`) REFERENCES `team_generation_runs`(`id`) ON DELETE SET NULL,
    INDEX `idx_teams_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 17. Team Members
CREATE TABLE IF NOT EXISTS `team_members` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `team_id` INT NOT NULL,
    `profile_id` INT NOT NULL,
    `assigned_role_id` INT,
    `matching_score` DECIMAL(5, 2) DEFAULT 0.00,
    `cluster_id` INT,
    `cluster_label` VARCHAR(100),
    `joined_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_team_student` (`team_id`, `profile_id`),
    FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`profile_id`) REFERENCES `student_profiles`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`assigned_role_id`) REFERENCES `roles`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 18. Role Assignments & Rationales
CREATE TABLE IF NOT EXISTS `role_assignments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `team_member_id` INT NOT NULL UNIQUE,
    `role_id` INT NOT NULL,
    `fit_score` DECIMAL(5, 2) NOT NULL,
    `rationale` TEXT NOT NULL,
    `is_overridden` BOOLEAN NOT NULL DEFAULT FALSE,
    `assigned_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`team_member_id`) REFERENCES `team_members`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 19. Evaluation Results (Side-by-side objective metrics)
CREATE TABLE IF NOT EXISTS `evaluation_results` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `run_id` INT NOT NULL UNIQUE,
    `project_id` INT NOT NULL,
    `method` ENUM('baseline', 'ml') NOT NULL,
    `skill_coverage_ratio` DECIMAL(5, 4) NOT NULL,
    `avg_skill_alignment` DECIMAL(5, 4) NOT NULL,
    `interest_alignment` DECIMAL(5, 4) NOT NULL,
    `experience_alignment` DECIMAL(5, 4) NOT NULL,
    `availability_compatibility` DECIMAL(5, 4) NOT NULL,
    `role_coverage` DECIMAL(5, 4) NOT NULL,
    `constraint_satisfaction_rate` DECIMAL(5, 4) NOT NULL,
    `team_size_compliance` DECIMAL(5, 4) NOT NULL,
    `assignment_completeness` DECIMAL(5, 4) NOT NULL,
    `unassigned_count` INT NOT NULL DEFAULT 0,
    `runtime_seconds` DECIMAL(8, 4) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`run_id`) REFERENCES `team_generation_runs`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
