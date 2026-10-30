import pytest
import numpy as np
from pathlib import Path
from models.entities import StudentProfile, Project
from services.student_service import StudentService
from ml.feature_pipeline import StudentFeaturePipeline
from ml.cluster_engine import StudentClusterEngine
from ml.ml_team_engine import MLGuidedTeamEngine
from config import Config

def test_feature_pipeline_fit_and_transform(db_session):
    catalogs = StudentService.get_all_catalogs(session=db_session)
    students = db_session.query(StudentProfile).all()

    pipeline = StudentFeaturePipeline()
    pipeline.fit_schema(
        skills=catalogs["skills"],
        interests=catalogs["interests"],
        slots=catalogs["slots"],
        roles=catalogs["roles"]
    )
    assert pipeline.is_fitted is True
    assert len(pipeline.feature_names) > 20

    X = pipeline.transform(students)
    assert isinstance(X, np.ndarray)
    assert X.shape[0] == len(students)
    assert X.shape[1] == len(pipeline.feature_names)
    assert np.isnan(X).sum() == 0  # No NaN values

def test_kmeans_clustering_and_persistence(db_session, tmp_path):
    catalogs = StudentService.get_all_catalogs(session=db_session)
    students = db_session.query(StudentProfile).all()

    pipeline = StudentFeaturePipeline()
    pipeline.fit_schema(
        skills=catalogs["skills"],
        interests=catalogs["interests"],
        slots=catalogs["slots"],
        roles=catalogs["roles"]
    )

    cluster_engine = StudentClusterEngine(n_clusters=4, random_state=42)
    cluster_engine.fit(students, pipeline)

    assert cluster_engine.is_fitted is True
    assert len(cluster_engine.cluster_labels) == len(students)
    assert len(cluster_engine.cluster_summaries) > 0
    assert cluster_engine.inertia_ > 0

    # Test persistence and reloading
    model_file = tmp_path / "test_kmeans.joblib"
    cluster_engine.save(filepath=model_file)
    assert model_file.exists()

    reloaded_engine = StudentClusterEngine.load(filepath=model_file)
    assert reloaded_engine is not None
    assert reloaded_engine.is_fitted is True

def test_ml_small_dataset_edge_case(db_session):
    catalogs = StudentService.get_all_catalogs(session=db_session)
    # Only 2 students
    students = db_session.query(StudentProfile).limit(2).all()

    pipeline = StudentFeaturePipeline()
    pipeline.fit_schema(
        skills=catalogs["skills"],
        interests=catalogs["interests"],
        slots=catalogs["slots"],
        roles=catalogs["roles"]
    )

    cluster_engine = StudentClusterEngine(n_clusters=4, random_state=42)
    cluster_engine.fit(students, pipeline)

    # Must safely handle small cohort with warning without throwing exception
    assert cluster_engine.is_fitted is True
    assert cluster_engine.insufficient_data_warning is not None

def test_ml_guided_team_generation(db_session):
    project = db_session.query(Project).filter_by(title="Intelligent HealthCare Analytics Portal").first()
    students = db_session.query(StudentProfile).all()
    catalogs = StudentService.get_all_catalogs(session=db_session)

    res = MLGuidedTeamEngine.generate_teams(
        eligible_students=students,
        project=project,
        catalogs=catalogs,
        n_clusters=4,
        random_seed=42
    )

    assert res["success"] is True
    assert res["n_teams"] > 0
    assert len(res["teams"]) == res["n_teams"]

    assigned_ids = set()
    for t in res["teams"]:
        assert len(t["members"]) == project.desired_team_size
        for m in t["members"]:
            assert m["profile_id"] not in assigned_ids
            assigned_ids.add(m["profile_id"])
            assert "explanation" in m
            assert len(m["explanation"]) > 0
            assert m["cluster_id"] is not None
