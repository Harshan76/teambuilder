"""
ml/feature_pipeline.py
====================================================================
Feature engineering and extraction pipeline for student profiles.
Transforms normalized relational student data into numerical matrices.
====================================================================
"""

import joblib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from config import Config
from models.entities import StudentProfile, Skill, Interest, AvailabilitySlot, Role

class StudentFeaturePipeline:
    def __init__(self):
        self.skill_names: List[str] = []
        self.interest_names: List[str] = []
        self.slot_names: List[str] = []
        self.role_names: List[str] = []
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def fit_schema(self, skills: List[Skill], interests: List[Interest], slots: List[AvailabilitySlot], roles: List[Role]):
        """Builds a consistent feature schema from database catalogs."""
        self.skill_names = sorted([s.name for s in skills])
        self.interest_names = sorted([i.name for i in interests])
        self.slot_names = sorted([s.slot_name for s in slots])
        self.role_names = sorted([r.name for r in roles])

        # Combined feature names list for model interpretability
        self.feature_names = (
            [f"skill_{name}" for name in self.skill_names] +
            [f"interest_{name}" for name in self.interest_names] +
            [f"slot_{name}" for name in self.slot_names] +
            [f"role_{name}" for name in self.role_names] +
            ["exp_level_normalized", "exp_years_normalized"]
        )
        self.is_fitted = True
        return self

    def transform(self, profiles: List[StudentProfile]) -> np.ndarray:
        """
        Transforms a cohort of StudentProfile instances into a 2D float NumPy matrix.
        Missing or incomplete values are cleanly imputed to zero/neutral.
        """
        if not self.is_fitted:
            raise RuntimeError("Feature pipeline must be fitted with catalog schema before transform.")

        matrix = []
        exp_level_map = {"Beginner": 0.33, "Intermediate": 0.66, "Advanced": 1.0}

        for p in profiles:
            row = []

            # 1. Technical Skills (Normalized proficiency 0.0 - 1.0)
            stu_skills = {ss.skill.name: ss.proficiency for ss in p.skills if ss.skill}
            for s_name in self.skill_names:
                prof = stu_skills.get(s_name, 0)
                row.append(round(prof / 5.0, 4))

            # 2. Domain Interests (Binary multi-hot 0.0 or 1.0)
            stu_interests = {si.interest.name for si in p.interests if si.interest}
            for i_name in self.interest_names:
                row.append(1.0 if i_name in stu_interests else 0.0)

            # 3. Availability Slots (Binary multi-hot 0.0 or 1.0)
            stu_slots = {sa.slot.slot_name for sa in p.availability if sa.slot}
            for slot_name in self.slot_names:
                row.append(1.0 if slot_name in stu_slots else 0.0)

            # 4. Preferred Roles (Ranked reciprocal weight: rank 1 = 1.0, rank 2 = 0.5, rank 3 = 0.33)
            stu_roles = {spr.role.name: spr.preference_rank for spr in p.preferred_roles if spr.role}
            for r_name in self.role_names:
                rank = stu_roles.get(r_name, 0)
                row.append(round(1.0 / rank, 4) if rank > 0 else 0.0)

            # 5. Experience level & years
            norm_exp_level = exp_level_map.get(p.experience_level, 0.33)
            norm_exp_years = min(1.0, max(0.0, float(p.experience_years or 0.0) / 5.0))
            row.append(norm_exp_level)
            row.append(norm_exp_years)

            matrix.append(row)

        return np.array(matrix, dtype=np.float32)

    def save(self, filepath: Path = None):
        target = filepath or (Config.ML_MODEL_DIR / "feature_pipeline.joblib")
        joblib.dump(self, target)

    @classmethod
    def load(cls, filepath: Path = None) -> "StudentFeaturePipeline":
        source = filepath or (Config.ML_MODEL_DIR / "feature_pipeline.joblib")
        if not source.exists():
            return None
        return joblib.load(source)
