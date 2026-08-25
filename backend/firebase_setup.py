"""Firebase Admin SDK initialization and auth dependency.

Uses Application Default Credentials (the same `gcloud auth application-default
login` credentials already set up for Vertex AI) -- no separate service account needed.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import auth, credentials, firestore
from fastapi import Header, HTTPException

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_app = firebase_admin.initialize_app(
    credentials.ApplicationDefault(),
    options={"projectId": os.environ["GOOGLE_CLOUD_PROJECT"]},
)

db = firestore.client()


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Verifies the Firebase ID token from the Authorization header and returns the uid."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired ID token")

    return decoded["uid"]
