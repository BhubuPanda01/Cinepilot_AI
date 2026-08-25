# CinePilot AI

**An autonomous pre-production studio for screenplays.** Upload a screenplay PDF and a
network of eight Gemini-powered agents turns it into a director-ready previsualization
package: scene breakdowns, character sheets, a storyboard with camera direction,
cinematic image prompts, web-grounded location intelligence, a critical review, and a
downloadable production report.

Built for the **Agentic Cinema hackathon — Parallel track**.

---

## What it does

Film pre-production is slow and expensive: storyboards, shot lists, character sheets,
location scouting, and risk assessment are all done by hand, over weeks. CinePilot
compresses that first pass into a few minutes.

The pipeline runs eight agents in sequence, each consuming the previous one's structured output:

| # | Agent | What it produces |
|---|-------|------------------|
| 1 | Parser | Scenes, sluglines, characters, action, dialogue |
| 2 | Scene Analysis | Emotion, action level, production complexity, safety risk |
| 3 | Character | Role, occupation, physical description, wardrobe, arc |
| 4 | Storyboard | 2–4 key frames per scene with shot type, angle, movement |
| 5 | Prompt Engineering | Cinematic image-generation prompts, consistent across frames |
| 6 | **Location Scout** | **Real filming permits, access rules and constraints, grounded in live web search** |
| 7 | Review | Pacing, camera variety, risk concentration, continuity findings |
| 8 | Director Report | Executive summary, recommendations, production notes, budget/risk |

Storyboard frames can then be rendered as actual images, and the whole package exported
as a formatted PDF.

---

## Google Cloud and Parallel at runtime

Both are genuinely called in code on every run, not just referenced here.

**Google Cloud — Gemini on Vertex AI**
- All eight agents are built with the **Google Agent Development Kit** (`google-adk`)
  and run on **Gemini 2.5 Flash** via **Vertex AI**.
  See [`backend/main.py`](backend/main.py) (`run_agent`) and [`backend/agents/`](backend/agents/).
- Storyboard images use **`gemini-2.5-flash-image`** on Vertex AI —
  [`backend/image_gen.py`](backend/image_gen.py).
- **Firestore** stores every project and job — [`backend/firebase_setup.py`](backend/firebase_setup.py),
  [`backend/jobs.py`](backend/jobs.py).
- **Firebase Auth** gates every endpoint via server-side ID token verification.
- **Cloud Storage** holds uploads and generated frames — [`backend/storage.py`](backend/storage.py).

**Parallel — Search API**
- The Location Scout Agent issues a live **Parallel Search API** call per distinct
  filming location on every parse — [`backend/parallel_search.py`](backend/parallel_search.py).
- Results are fed to the agent in [`backend/agents/location_scout_agent.py`](backend/agents/location_scout_agent.py),
  which is instructed to ground its findings strictly in the retrieved excerpts and to
  return `grounded: false` with no sources when the web turns up nothing useful — so a
  fictional location never gets an invented permit authority.

A real example from the included demo screenplay: for *Varanasi Railway Station*, the
agent surfaced Indian Railways' platform access-control policy and India's Ministry of
External Affairs filming permission rules, with source URLs, and correctly reported "no
sources found" for the screenplay's fictional locations.

---

## Tech stack

- **Frontend** — Next.js 16, React, Tailwind CSS, Firebase Auth
- **Backend** — FastAPI (Python), Google Agent Development Kit
- **AI** — Gemini 2.5 Flash and `gemini-2.5-flash-image` on Vertex AI
- **Data** — Cloud Firestore, Cloud Storage
- **Partner** — Parallel Search API
- **Hosting** — Cloud Run (backend), Firebase Hosting (frontend)

---

## Running it locally

### Prerequisites

- Python 3.10+ and Node.js 18+
- A Google Cloud project with **Vertex AI** enabled and billing active
- A Firebase project (same GCP project) with **Google Sign-In** and **Firestore** enabled
- The [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- A [Parallel](https://platform.parallel.ai) API key

### 1. Authenticate to Google Cloud

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Configure environment

Copy `.env.example` to `.env` in the repository root and fill it in:

```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
PARALLEL_API_KEY=your-parallel-api-key
```

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

### 4. Frontend

Add your Firebase web config to `frontend/src/lib/firebase.ts`, then:

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE=http://localhost:8001" > .env.local
npm run dev
```

Open <http://localhost:3000>, sign in with Google, and upload a screenplay PDF.
A sample is included at `backend/uploads/`.

### Command line

The pipeline also runs standalone, without the web app:

```bash
cd backend
python main.py path/to/screenplay.pdf
```

---

## Deploying

**Backend → Cloud Run**

```bash
gcloud run deploy cinepilot-backend \
  --source=backend --region=us-central1 \
  --service-account=YOUR_SERVICE_ACCOUNT \
  --no-cpu-throttling \
  --min-instances=0 --max-instances=3 \
  --memory=1Gi --timeout=900 \
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT,GOOGLE_CLOUD_LOCATION=us-central1,GCS_BUCKET=YOUR_BUCKET,ALLOWED_ORIGINS=https://your-frontend-domain \
  --set-secrets=PARALLEL_API_KEY=parallel-api-key:latest \
  --allow-unauthenticated
```

`--no-cpu-throttling` matters: parsing continues in the background after the request
returns, and Cloud Run's default only allocates CPU during request processing, which
would freeze the pipeline mid-run.

The service account needs `roles/aiplatform.user`, `roles/datastore.user`,
`roles/storage.objectAdmin`, and `roles/secretmanager.secretAccessor`.

**Frontend → Firebase Hosting**

```bash
cd frontend
npm run build
firebase deploy --only hosting
```

Add the resulting domain to **Firebase Console → Authentication → Settings → Authorized
domains**, and pass it to the backend via `ALLOWED_ORIGINS`.

---

## Repository layout

```
backend/
  agents/              8 ADK agent definitions
  main.py              pipeline orchestration + retry/backoff
  app.py               FastAPI routes, auth, job lifecycle
  parallel_search.py   Parallel Search API client
  image_gen.py         Gemini image generation on Vertex AI
  storage.py           Cloud Storage (local fallback for dev)
  jobs.py              Firestore-backed progress tracking
  pdf_export.py        production package PDF
  firebase_setup.py    Admin SDK init + ID token verification
frontend/
  src/app/page.tsx     dashboard
  src/components/      landing page, loader, progress, authed images
  src/lib/             Firebase client + auth context
```

---

## Notes

- Free-tier Vertex AI quotas are low; the pipeline makes eight model calls per parse and
  retries with backoff on `429 RESOURCE_EXHAUSTED`. Retry logs are expected, not errors.
- Image generation is the largest per-run cost. It is a separate, opt-in action rather
  than part of the parse.
- `.env` is gitignored. No credentials are committed.

## License

[MIT](LICENSE)
