"""Storyboard frame image generation using Gemini's native image generation on Vertex AI.

Authenticates the same way as every other agent -- Application Default Credentials
locally, the service account identity on Cloud Run -- so no API key is involved.
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

IMAGE_MODEL = "gemini-2.5-flash-image"

_client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
)


def generate_frame_image(prompt: str) -> bytes:
    response = _client.models.generate_content(model=IMAGE_MODEL, contents=prompt)
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data
    raise RuntimeError("Gemini did not return an image for this prompt")


async def generate_frame_image_with_retry(prompt: str, max_retries: int = 3) -> bytes:
    for attempt in range(max_retries):
        try:
            return await asyncio.to_thread(generate_frame_image, prompt)
        except ClientError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait_seconds = 20 * (attempt + 1)
                logger.warning(
                    "Image generation quota hit; retrying in %ss (attempt %s/%s)",
                    wait_seconds,
                    attempt + 1,
                    max_retries,
                    extra={"event": "image_quota_retry", "attempt": attempt + 1},
                )
                await asyncio.sleep(wait_seconds)
                continue
            raise
