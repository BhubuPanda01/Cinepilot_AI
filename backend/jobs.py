"""Parse-job progress tracking, stored in Firestore.

An in-memory dict only works when exactly one process serves every request. On
Cloud Run a progress poll can land on a different instance than the one running the
job, so job state lives beside the user's projects instead.
"""

import logging
import uuid

from google.cloud.firestore import SERVER_TIMESTAMP

from firebase_setup import db

logger = logging.getLogger(__name__)


def _doc(uid: str, job_id: str):
    return db.collection("users").document(uid).collection("jobs").document(job_id)


def create_job(uid: str, total_steps: int) -> str:
    job_id = uuid.uuid4().hex
    _doc(uid, job_id).set(
        {
            "status": "running",
            "step": 0,
            "total_steps": total_steps,
            "step_name": "Starting...",
            "project_id": None,
            "error": None,
            "created_at": SERVER_TIMESTAMP,
        }
    )
    return job_id


def update_progress(uid: str, job_id: str, step: int, step_name: str) -> None:
    _doc(uid, job_id).update({"step": step, "step_name": step_name})


def complete_job(uid: str, job_id: str, project_id: str) -> None:
    _doc(uid, job_id).update({"status": "done", "project_id": project_id})


def fail_job(uid: str, job_id: str, error: str) -> None:
    _doc(uid, job_id).update({"status": "error", "error": error})


def get_job(uid: str, job_id: str) -> dict | None:
    snapshot = _doc(uid, job_id).get()
    if not snapshot.exists:
        return None

    job = snapshot.to_dict()
    # created_at is a Firestore timestamp and isn't JSON-serializable.
    job.pop("created_at", None)
    return job
