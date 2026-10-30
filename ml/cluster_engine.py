"""
ml/cluster_engine.py
====================================================================
Scikit-Learn K-Means Student Profile Clustering Engine.
Discovers latent student archetypes from profile feature vectors.
====================================================================
"""

import json
import logging
import joblib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from config import Config
from models.entities import StudentProfile, ModelRun
from ml.feature_pipeline import StudentFeaturePipeline
from database.db import get_db

logger = logging.getLogger(__name__)

class StudentClusterEngine:
    def __init__(self, n_clusters: int = 4, random_state: int = 42):
        self.requested_n_clusters = n_clusters
        self.random_state = random_state
        self.model: KMeans = None
        self.pipeline: StudentFeaturePipeline = None
        self.cluster_labels: np.ndarray = None
        self.cluster_summaries: Dict[int, Dict[str, Any]] = {}
        self.silhouette_score_: float = None
        self.inertia_: float = None
        self.is_fitted: bool = False
        self.insufficient_data_warning: str = None

    def fit(self, profiles: List[StudentProfile], pipeline: StudentFeaturePipeline) -> "StudentClusterEngine":
        """
        Fits the Scikit-learn KMeans model on the student feature matrix.
        Safely handles small cohorts and extracts interpretable archetypes.
        """
        self.pipeline = pipeline
        n_samples = len(profiles)

        # Edge case: Insufficient data (< 4 students)
        if n_samples < 4:
            self.insufficient_data_warning = (
                f"Cohort size is too small ({n_samples} students) for multi-cluster statistical discovery. "
                "Minimum 4 profiles required. Grouping into a single generalist cohort."
            )
            logger.warning(self.insufficient_data_warning)
            self.cluster_labels = np.zeros(n_samples, dtype=int)
            self.cluster_summaries[0] = {
                "name": "Generalist Cohort (Small Sample Fallback)",
                "size": n_samples,
                "top_skills": ["Diverse Skills"],
                "top_interests": ["Broad Interests"],
                "dominant_role": "Multi-disciplinary"
            }
            self.is_fitted = True
            return self

        # Determine safe k bounded by sample size
        k = min(self.requested_n_clusters, max(2, n_samples // 3), 6)
        if k >= n_samples:
            k = max(2, n_samples - 1)

        X = self.pipeline.transform(profiles)

        # Fit Scikit-Learn KMeans
        self.model = KMeans(
            n_clusters=k,
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )
        self.cluster_labels = self.model.fit_predict(X)
        self.inertia_ = float(self.model.inertia_)

        # Compute Silhouette Score if k >= 2 and samples > k
        if k >= 2 and n_samples > k:
            try:
                self.silhouette_score_ = float(silhouette_score(X, self.cluster_labels))
            except Exception as e:
                logger.warning(f"Could not compute silhouette score: {e}")
                self.silhouette_score_ = 0.0
        else:
            self.silhouette_score_ = 0.0

        # Generate interpretable cluster archetype summaries
        self._generate_cluster_summaries(X, profiles)
        self.is_fitted = True

        return self

    def _generate_cluster_summaries(self, X: np.ndarray, profiles: List[StudentProfile]):
        """
        Analyzes cluster centroids and feature values to generate human-readable archetype names.
        """
        feature_names = self.pipeline.feature_names
        centroids = self.model.cluster_centers_

        for cluster_id in range(self.model.n_clusters):
            center = centroids[cluster_id]
            members = [profiles[i] for i, lbl in enumerate(self.cluster_labels) if lbl == cluster_id]
            size = len(members)

            # Find top skills in this cluster centroid
            skill_indices = [idx for idx, name in enumerate(feature_names) if name.startswith("skill_")]
            top_skill_idx = sorted(skill_indices, key=lambda idx: center[idx], reverse=True)[:3]
            top_skills = [
                f"{feature_names[idx].replace('skill_', '')} (avg {round(center[idx] * 5.0, 1)}/5)"
                for idx in top_skill_idx if center[idx] > 0.1
            ]

            # Find top interests
            interest_indices = [idx for idx, name in enumerate(feature_names) if name.startswith("interest_")]
            top_int_idx = sorted(interest_indices, key=lambda idx: center[idx], reverse=True)[:2]
            top_interests = [
                feature_names[idx].replace("interest_", "")
                for idx in top_int_idx if center[idx] > 0.1
            ]

            # Find dominant role
            role_indices = [idx for idx, name in enumerate(feature_names) if name.startswith("role_")]
            top_role_idx = sorted(role_indices, key=lambda idx: center[idx], reverse=True)[:1]
            dominant_role = (
                feature_names[top_role_idx[0]].replace("role_", "")
                if top_role_idx and center[top_role_idx[0]] > 0.05
                else "Fullstack Generalist"
            )

            # Determine human-readable archetype title
            title = self._derive_archetype_title(top_skills, dominant_role)

            self.cluster_summaries[cluster_id] = {
                "name": f"Cluster {cluster_id}: {title}",
                "title": title,
                "size": size,
                "top_skills": top_skills or ["General Engineering"],
                "top_interests": top_interests or ["Software Development"],
                "dominant_role": dominant_role
            }

    def _derive_archetype_title(self, top_skills: List[str], dominant_role: str) -> str:
        skills_str = " ".join(top_skills).lower()
        if "scikit" in skills_str or "pandas" in skills_str or "pytorch" in skills_str or "data" in dominant_role.lower():
            return "Data Science & Machine Learning Specialist"
        elif "react" in skills_str or "javascript" in skills_str or "figma" in skills_str or "frontend" in dominant_role.lower() or "ui" in dominant_role.lower():
            return "Frontend & UI/UX Specialist"
        elif "python" in skills_str or "sql" in skills_str or "flask" in skills_str or "django" in skills_str or "backend" in dominant_role.lower():
            return "Backend & Systems Specialist"
        elif "docker" in skills_str or "linux" in skills_str or "git" in skills_str or "testing" in dominant_role.lower() or "qa" in dominant_role.lower():
            return "DevOps, QA & Architecture Specialist"
        elif "coordinator" in dominant_role.lower() or "researcher" in dominant_role.lower():
            return "Project Coordinator & Research Lead"
        else:
            return f"Fullstack Specialist ({dominant_role})"

    def predict(self, profiles: List[StudentProfile]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        if self.model is None:
            return np.zeros(len(profiles), dtype=int)
        X = self.pipeline.transform(profiles)
        return self.model.predict(X)

    def save(self, filepath: Path = None, db_session = None):
        """Saves fitted model to joblib and records run metadata into database."""
        target_path = filepath or (Config.ML_MODEL_DIR / "kmeans_model.joblib")
        joblib.dump(self, target_path)

        # Log into model_runs table if db_session is provided
        try:
            db = db_session or get_db()
            run = ModelRun(
                algorithm="K-Means (Scikit-Learn)",
                n_clusters=self.model.n_clusters if self.model else 1,
                silhouette_score=self.silhouette_score_,
                inertia=self.inertia_,
                n_samples=len(self.cluster_labels) if self.cluster_labels is not None else 0,
                features_json=json.dumps(self.cluster_summaries),
                model_file_path=str(target_path),
                is_active=True
            )
            db.add(run)
            db.commit()
        except Exception as e:
            logger.warning(f"Could not record model run to database: {e}")

    @classmethod
    def load(cls, filepath: Path = None) -> "StudentClusterEngine":
        source = filepath or (Config.ML_MODEL_DIR / "kmeans_model.joblib")
        if not source.exists():
            return None
        return joblib.load(source)
