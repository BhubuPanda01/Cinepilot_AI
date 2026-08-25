"""CinePilot AI API: upload a screenplay PDF, run the agent pipeline, persist per-user projects.

Local:
    uvicorn app:app --reload --port 8001
Cloud Run:
    uvicorn app:app --host 0.0.0.0 --port $PORT
"""

import asyncio
import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from google.cloud.firestore import SERVER_TIMESTAMP

import jobs as job_store
import storage
from firebase_setup import db, get_current_user
from image_gen import generate_frame_image_with_retry
from main import PIPELINE_STEPS, extract_text_from_bytes, run_pipeline
from pdf_export import build_production_pdf

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CinePilot AI API")

# Additional browser origins allowed to call this API (the deployed frontend).
EXTRA_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", *EXTRA_ORIGINS],
    allow_methods=["*"],
    allow_headers=["*"],
)


def projects_collection(uid: str):
    return db.collection("users").document(uid).collection("projects")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/projects")
def list_projects(uid: str = Depends(get_current_user)):
    docs = projects_collection(uid).order_by(
        "created_at", direction="DESCENDING"
    ).stream()
    return [
        {"id": doc.id, "name": doc.get("name"), "created_at": _iso(doc.get("created_at"))}
        for doc in docs
    ]


@app.get("/api/projects/{project_id}")
def get_project(project_id: str, uid: str = Depends(get_current_user)):
    doc = projects_collection(uid).document(project_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"id": doc.id, "name": doc.get("name"), "data": doc.get("data")}


@app.post("/api/parse")
async def parse_screenplay(
    file: UploadFile = File(...), uid: str = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    stem = Path(file.filename).stem

    storage.write_upload(f"{uid}/uploads/{uuid.uuid4().hex[:8]}_{file.filename}", content)

    job_id = job_store.create_job(uid, len(PIPELINE_STEPS))
    asyncio.create_task(_run_parse_job(job_id, uid, stem, content))

    return {"job_id": job_id}


async def _run_parse_job(job_id: str, uid: str, stem: str, content: bytes):
    try:
        text = extract_text_from_bytes(content)

        async def on_progress(step: int, step_name: str):
            job_store.update_progress(uid, job_id, step, step_name)

        result = await run_pipeline(text, on_progress=on_progress)

        doc_ref = projects_collection(uid).document()
        doc_ref.set({"name": stem, "created_at": SERVER_TIMESTAMP, "data": result})

        job_store.complete_job(uid, job_id, doc_ref.id)
        logger.info(
            "Parse job finished for %s", stem, extra={"event": "parse_complete"}
        )
    except Exception as e:
        logger.exception("Parse job failed", extra={"event": "parse_failed"})
        job_store.fail_job(uid, job_id, str(e))


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, uid: str = Depends(get_current_user)):
    job = job_store.get_job(uid, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/projects/{project_id}/generate-images")
async def generate_images(project_id: str, uid: str = Depends(get_current_user)):
    doc_ref = projects_collection(uid).document(project_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Project not found")

    data = doc.get("data")
    failed_frames = []

    for scene in data.get("scenes", []):
        for frame in scene.get("storyboard", []):
            if not frame.get("prompt") or frame.get("image_path"):
                continue  # no prompt to render, or already generated

            filename = f"scene{scene['scene_number']}_frame{frame['frame_number']}.png"
            object_path = f"{uid}/{project_id}/{filename}"
            try:
                image_bytes = await generate_frame_image_with_retry(frame["prompt"])
            except Exception:
                logger.warning(
                    "Frame generation failed: %s",
                    filename,
                    extra={"event": "frame_failed"},
                )
                failed_frames.append(filename)
                continue

            storage.write_media(object_path, image_bytes)
            frame["image_path"] = f"/api/media/{object_path}"
            # Persist after each frame so a later failure never discards images
            # already generated -- image generation can fail partway through a batch.
            doc_ref.update({"data": data})
            await asyncio.sleep(3)  # light throttle across many frames

    return {"id": project_id, "data": data, "failed_frames": failed_frames}


@app.get("/api/media/{uid}/{project_id}/{filename}")
def get_media(
    uid: str,
    project_id: str,
    filename: str,
    caller_uid: str = Depends(get_current_user),
):
    """Serve a generated frame. Authenticated so one user cannot read another's storyboards."""
    if uid != caller_uid:
        raise HTTPException(status_code=403, detail="Forbidden")

    data = storage.read_media(f"{uid}/{project_id}/{filename}")
    if data is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=data, media_type="image/png")


@app.get("/api/projects/{project_id}/export-pdf")
def export_pdf(project_id: str, uid: str = Depends(get_current_user)):
    doc = projects_collection(uid).document(project_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Project not found")

    pdf_bytes = build_production_pdf(doc.get("name"), doc.get("data"))
    filename = f"{doc.get('name')}_production_package.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _iso(timestamp):
    return timestamp.isoformat() if timestamp else None
