"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import { useAuth } from "@/lib/AuthContext";
import { AuthedImage } from "@/components/AuthedImage";
import { CinePilotLoader } from "@/components/CinePilotLoader";
import { LandingPage } from "@/components/LandingPage";
import { PipelineProgress, ParseProgress } from "@/components/PipelineProgress";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8002";

type SceneAnalysis = {
  emotion: string;
  action_level: string;
  complexity: string;
  risk_level: string;
  risk_notes: string;
};

type StoryboardFrame = {
  scene_number: number;
  frame_number: number;
  shot_type: string;
  camera_angle: string;
  camera_movement: string | null;
  description: string;
  prompt: string | null;
  negative_prompt: string | null;
  image_path?: string | null;
};

type Scene = {
  scene_number: number;
  heading: string;
  location: string;
  time_of_day: string;
  characters: string[];
  action: string;
  dialogue: string[];
  analysis?: SceneAnalysis;
  storyboard?: StoryboardFrame[];
};

function levelColor(level: string | undefined) {
  switch (level?.toLowerCase()) {
    case "high":
      return "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300";
    case "medium":
      return "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300";
    case "low":
      return "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300";
    default:
      return "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300";
  }
}

type CharacterProfile = {
  name: string;
  occupation: string;
  role: string;
  physical_description: string;
  personality: string;
  wardrobe_style: string;
  arc_summary: string;
};

type ReviewFinding = {
  category: string;
  severity: string;
  note: string;
};

type Review = {
  overall_assessment: string;
  strengths: string[];
  findings: ReviewFinding[];
};

type DirectorReport = {
  executive_summary: string;
  key_recommendations: string[];
  production_notes: string[];
  budget_risk_summary: string;
};

type LocationIntel = {
  location: string;
  scene_numbers: number[];
  permit_notes: string;
  logistical_challenges: string;
  practical_recommendations: string;
  sources: string[];
  grounded: boolean;
};

type ParsedScreenplay = {
  title: string | null;
  scenes: Scene[];
  characters?: CharacterProfile[];
  location_scout?: LocationIntel[];
  review?: Review;
  director_report?: DirectorReport;
};

function roleColor(role: string | undefined) {
  switch (role?.toLowerCase()) {
    case "protagonist":
      return "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300";
    case "antagonist":
      return "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300";
    case "supporting":
      return "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300";
    default:
      return "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300";
  }
}

type ProjectSummary = {
  id: string;
  name: string;
  created_at: string | null;
};

export default function Home() {
  const { user, loading: authLoading, signInWithGoogle, signOut } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<ParseProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ParsedScreenplay | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const [imagesLoading, setImagesLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function authHeader() {
    if (!user) throw new Error("Not signed in");
    const token = await user.getIdToken();
    return { Authorization: `Bearer ${token}` };
  }

  async function refreshProjects() {
    if (!user) return;
    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        headers: await authHeader(),
      });
      setProjects(await res.json());
    } catch {
      setProjects([]);
    }
  }

  useEffect(() => {
    refreshProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file || !user) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setProgress({ step: 0, total_steps: 7, step_name: "Uploading screenplay..." });

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/api/parse`, {
        method: "POST",
        headers: await authHeader(),
        body: formData,
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Request failed (${res.status})`);
      }

      const { job_id } = await res.json();
      const header = await authHeader();

      pollRef.current = setInterval(async () => {
        try {
          const jobRes = await fetch(`${API_BASE}/api/jobs/${job_id}`, { headers: header });
          const job = await jobRes.json();

          if (job.status === "running") {
            setProgress({ step: job.step, total_steps: job.total_steps, step_name: job.step_name });
          } else if (job.status === "done") {
            if (pollRef.current) clearInterval(pollRef.current);
            // The job record only carries the project id -- a full parsed
            // screenplay would not reliably fit in a single Firestore document.
            const projectRes = await fetch(
              `${API_BASE}/api/projects/${job.project_id}`,
              { headers: header }
            );
            const project = await projectRes.json();
            setResult(project.data);
            setCurrentProjectId(job.project_id);
            setLoading(false);
            setProgress(null);
            await refreshProjects();
          } else if (job.status === "error") {
            if (pollRef.current) clearInterval(pollRef.current);
            setError(job.error ?? "Something went wrong");
            setLoading(false);
            setProgress(null);
          }
        } catch {
          // transient network hiccup while polling -- keep trying on the next tick
        }
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
      setProgress(null);
    }
  }

  async function loadProject(id: string) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${id}`, {
        headers: await authHeader(),
      });
      if (!res.ok) throw new Error("Could not load project");
      const data = await res.json();
      setResult(data.data);
      setCurrentProjectId(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function generateImages() {
    if (!currentProjectId) return;
    setImagesLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/projects/${currentProjectId}/generate-images`,
        { method: "POST", headers: await authHeader() }
      );
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Request failed (${res.status})`);
      }
      const data = await res.json();
      setResult(data.data);
      if (data.failed_frames && data.failed_frames.length > 0) {
        setError(
          `${data.failed_frames.length} frame(s) failed to generate (likely a quota limit): ${data.failed_frames.join(", ")}. Click "Generate Storyboard Images" again to retry just those.`
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setImagesLoading(false);
    }
  }

  async function downloadPdf() {
    if (!currentProjectId) return;
    setPdfLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/projects/${currentProjectId}/export-pdf`,
        { headers: await authHeader() }
      );
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Request failed (${res.status})`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${result?.title ?? "production_package"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setPdfLoading(false);
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950">
        <CinePilotLoader label="Warming up the studio..." />
      </div>
    );
  }

  if (!user) {
    return <LandingPage onSignIn={signInWithGoogle} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-black px-6 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <span className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                CinePilot AI
              </span>
              <span className="text-zinc-400 dark:text-zinc-600 font-normal"> &mdash; Pre-Production Pipeline</span>
            </h1>
            <p className="mt-1 text-sm text-zinc-500">
              Upload a screenplay PDF: Parser &rarr; Scene Analysis &rarr; Characters &rarr; Storyboard &rarr; Prompts &rarr; Review &rarr; Director Report.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-500 shrink-0">
            <span>{user.displayName ?? user.email}</span>
            <button
              onClick={() => signOut()}
              className="rounded-md border border-zinc-300 dark:border-zinc-700 px-2 py-1 hover:bg-zinc-100 dark:hover:bg-zinc-900"
            >
              Sign out
            </button>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="mt-6 flex flex-col items-center gap-4 rounded-2xl border-2 border-dashed border-zinc-300 dark:border-zinc-700 bg-white/50 dark:bg-zinc-950/50 backdrop-blur p-8 text-center hover:border-indigo-300 dark:hover:border-indigo-800 transition-colors"
        >
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm text-zinc-700 dark:text-zinc-300"
          />
          <button
            type="submit"
            disabled={!file || loading}
            className="rounded-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 px-6 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/20 disabled:opacity-40 disabled:shadow-none hover:shadow-indigo-500/40 transition-shadow"
          >
            {loading ? "Working..." : "Parse Screenplay"}
          </button>
        </form>

        {loading && progress && (
          <div className="mt-4">
            <PipelineProgress progress={progress} />
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-md bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-300">
            {error}
          </div>
        )}

        {projects.length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
              Your projects
            </h2>
            <ul className="mt-2 flex flex-wrap gap-2">
              {projects.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => loadProject(p.id)}
                    className="rounded-full bg-zinc-200 dark:bg-zinc-800 px-3 py-1 text-xs text-zinc-700 dark:text-zinc-300 hover:bg-zinc-300 dark:hover:bg-zinc-700"
                  >
                    {p.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result && (
          <div className="mt-8">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                {result.title ?? "Untitled Screenplay"}
              </h2>
              <button
                onClick={downloadPdf}
                disabled={pdfLoading || !currentProjectId}
                className="rounded-md bg-zinc-900 dark:bg-zinc-100 px-3 py-1.5 text-xs font-medium text-white dark:text-black disabled:opacity-40"
              >
                {pdfLoading ? "Generating PDF..." : "Download Production Package (PDF)"}
              </button>
            </div>

            {result.characters && result.characters.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                  Characters
                </h3>
                <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {result.characters.map((c) => (
                    <div
                      key={c.name}
                      className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-4 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-zinc-800 dark:text-zinc-100">
                          {c.name}
                        </span>
                        <span className={`rounded-full px-2 py-0.5 text-xs ${roleColor(c.role)}`}>
                          {c.role}
                        </span>
                      </div>
                      <p className="mt-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                        {c.occupation}
                      </p>
                      <p className="mt-2 text-xs text-zinc-600 dark:text-zinc-400">
                        {c.physical_description}
                      </p>
                      <p className="mt-1 text-xs text-zinc-500">
                        <span className="font-medium">Personality:</span> {c.personality}
                      </p>
                      <p className="mt-1 text-xs text-zinc-500">
                        <span className="font-medium">Wardrobe:</span> {c.wardrobe_style}
                      </p>
                      <p className="mt-1 text-xs italic text-zinc-500">
                        {c.arc_summary}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6 flex items-center justify-between">
              <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                Scenes
              </h3>
              <button
                onClick={generateImages}
                disabled={imagesLoading || !currentProjectId}
                className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-40"
              >
                {imagesLoading ? "Generating images..." : "Generate Storyboard Images"}
              </button>
            </div>
            <div className="mt-2 flex flex-col gap-4">
              {result.scenes.map((scene) => (
                <div
                  key={scene.scene_number}
                  className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="font-medium text-zinc-800 dark:text-zinc-100">
                    Scene {scene.scene_number}: {scene.heading}
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">
                    {scene.location} &middot; {scene.time_of_day}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {scene.characters.map((c) => (
                      <span
                        key={c}
                        className="rounded-full bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 text-xs text-zinc-600 dark:text-zinc-300"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                  {scene.analysis && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <span className="rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 px-2 py-0.5 text-xs">
                        {scene.analysis.emotion}
                      </span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${levelColor(scene.analysis.action_level)}`}>
                        Action: {scene.analysis.action_level}
                      </span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${levelColor(scene.analysis.complexity)}`}>
                        Complexity: {scene.analysis.complexity}
                      </span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${levelColor(scene.analysis.risk_level)}`}>
                        Risk: {scene.analysis.risk_level}
                      </span>
                    </div>
                  )}
                  <p className="mt-3 text-sm text-zinc-700 dark:text-zinc-300">
                    {scene.action}
                  </p>
                  {scene.analysis?.risk_notes && scene.analysis.risk_notes.toLowerCase() !== "none" && (
                    <p className="mt-1 text-xs text-zinc-500">
                      Risk note: {scene.analysis.risk_notes}
                    </p>
                  )}
                  {scene.dialogue.length > 0 && (
                    <div className="mt-2 text-sm italic text-zinc-500">
                      {scene.dialogue.map((d, i) => (
                        <div key={i}>{d}</div>
                      ))}
                    </div>
                  )}
                  {scene.storyboard && scene.storyboard.length > 0 && (
                    <div className="mt-4 border-t border-zinc-100 dark:border-zinc-800 pt-3">
                      <div className="text-xs font-medium text-zinc-500 mb-2">Storyboard</div>
                      <div className="flex flex-col gap-2">
                        {scene.storyboard.map((frame) => (
                          <div
                            key={frame.frame_number}
                            className="rounded-md bg-zinc-50 dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 p-3"
                          >
                            <div className="flex flex-wrap items-center gap-1.5 text-xs">
                              <span className="font-medium text-zinc-700 dark:text-zinc-300">
                                Frame {frame.frame_number}
                              </span>
                              <span className="rounded-full bg-zinc-200 dark:bg-zinc-800 px-2 py-0.5 text-zinc-600 dark:text-zinc-300">
                                {frame.shot_type}
                              </span>
                              <span className="rounded-full bg-zinc-200 dark:bg-zinc-800 px-2 py-0.5 text-zinc-600 dark:text-zinc-300">
                                {frame.camera_angle}
                              </span>
                              {frame.camera_movement && (
                                <span className="rounded-full bg-zinc-200 dark:bg-zinc-800 px-2 py-0.5 text-zinc-600 dark:text-zinc-300">
                                  {frame.camera_movement}
                                </span>
                              )}
                            </div>
                            <p className="mt-1.5 text-xs text-zinc-600 dark:text-zinc-400">
                              {frame.description}
                            </p>
                            {frame.prompt && (
                              <p className="mt-1.5 text-xs italic text-zinc-500">
                                Prompt: {frame.prompt}
                              </p>
                            )}
                            {frame.image_path && (
                              <AuthedImage
                                path={frame.image_path}
                                alt={frame.description}
                                apiBase={API_BASE}
                                className="mt-2 rounded-md w-full max-w-sm"
                              />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {result.location_scout && result.location_scout.length > 0 && (
              <div className="mt-8">
                <div className="flex items-baseline justify-between">
                  <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                    Location Intelligence
                  </h3>
                  <span className="text-xs text-zinc-400">
                    Web-grounded via Parallel Search
                  </span>
                </div>
                <div className="mt-2 flex flex-col gap-3">
                  {result.location_scout.map((loc) => (
                    <div
                      key={loc.location}
                      className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-zinc-800 dark:text-zinc-100">
                          {loc.location}
                        </span>
                        <span className="text-xs text-zinc-500">
                          Scene{loc.scene_numbers.length > 1 ? "s" : ""}{" "}
                          {loc.scene_numbers.join(", ")}
                        </span>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${
                            loc.grounded
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                              : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
                          }`}
                        >
                          {loc.grounded ? "Sourced" : "No sources found"}
                        </span>
                      </div>

                      {loc.grounded ? (
                        <>
                          <p className="mt-3 text-xs text-zinc-600 dark:text-zinc-400">
                            <span className="font-medium text-zinc-700 dark:text-zinc-300">
                              Permits:
                            </span>{" "}
                            {loc.permit_notes}
                          </p>
                          <p className="mt-1.5 text-xs text-zinc-600 dark:text-zinc-400">
                            <span className="font-medium text-zinc-700 dark:text-zinc-300">
                              Constraints:
                            </span>{" "}
                            {loc.logistical_challenges}
                          </p>
                          <p className="mt-1.5 text-xs text-zinc-600 dark:text-zinc-400">
                            <span className="font-medium text-zinc-700 dark:text-zinc-300">
                              Recommendations:
                            </span>{" "}
                            {loc.practical_recommendations}
                          </p>
                          <div className="mt-3 flex flex-col gap-1">
                            <span className="text-xs font-medium text-zinc-500">
                              Sources
                            </span>
                            {loc.sources.map((url) => (
                              <a
                                key={url}
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline break-all"
                              >
                                {url}
                              </a>
                            ))}
                          </div>
                        </>
                      ) : (
                        <p className="mt-2 text-xs text-zinc-500">
                          No reliable web sources found &mdash; likely a fictional or generic
                          location. Nothing was inferred.
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.review && (
              <div className="mt-8">
                <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                  Review
                </h3>
                <div className="mt-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm">
                  <p className="text-sm text-zinc-700 dark:text-zinc-300">
                    {result.review.overall_assessment}
                  </p>

                  {result.review.strengths.length > 0 && (
                    <div className="mt-3">
                      <div className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                        Strengths
                      </div>
                      <ul className="mt-1 list-disc list-inside text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                        {result.review.strengths.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.review.findings.length > 0 && (
                    <div className="mt-3">
                      <div className="text-xs font-medium text-zinc-500">Findings</div>
                      <div className="mt-1 flex flex-col gap-2">
                        {result.review.findings.map((f, i) => (
                          <div key={i} className="text-xs">
                            <span className={`rounded-full px-2 py-0.5 mr-2 ${levelColor(f.severity)}`}>
                              {f.severity}
                            </span>
                            <span className="font-medium text-zinc-700 dark:text-zinc-300">
                              {f.category}:
                            </span>{" "}
                            <span className="text-zinc-600 dark:text-zinc-400">{f.note}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {result.director_report && (
              <div className="mt-6">
                <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                  Director Report
                </h3>
                <div className="mt-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm">
                  <p className="text-sm text-zinc-700 dark:text-zinc-300">
                    {result.director_report.executive_summary}
                  </p>

                  <div className="mt-3">
                    <div className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                      Key Recommendations
                    </div>
                    <ul className="mt-1 list-disc list-inside text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                      {result.director_report.key_recommendations.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="mt-3">
                    <div className="text-xs font-medium text-zinc-500">Production Notes</div>
                    <ul className="mt-1 list-disc list-inside text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
                      {result.director_report.production_notes.map((n, i) => (
                        <li key={i}>{n}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="mt-3">
                    <div className="text-xs font-medium text-zinc-500">Budget/Risk Summary</div>
                    <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                      {result.director_report.budget_risk_summary}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
