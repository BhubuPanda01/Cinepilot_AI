"use client";

const PIPELINE = [
  { icon: "📄", name: "Parser Agent", desc: "Extracts scenes, characters, locations & dialogue from your PDF" },
  { icon: "🎭", name: "Scene Analysis", desc: "Rates emotion, action level, complexity & risk per scene" },
  { icon: "🧑‍🤝‍🧑", name: "Character Agent", desc: "Builds concept profiles: role, look, personality, wardrobe" },
  { icon: "🎬", name: "Storyboard Agent", desc: "Breaks every scene into key shots with camera direction" },
  { icon: "✍️", name: "Prompt Agent", desc: "Writes cinematic image-generation prompts per frame" },
  { icon: "🔍", name: "Review Agent", desc: "Critiques pacing, camera variety, risk load & consistency" },
  { icon: "📋", name: "Director Report", desc: "Synthesizes everything into recommendations & production notes" },
];

export function LandingPage({ onSignIn }: { onSignIn: () => void }) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 overflow-hidden relative">
      {/* Ambient gradient glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-indigo-600/30 blur-3xl" />
        <div className="absolute top-20 -right-40 h-96 w-96 rounded-full bg-pink-600/20 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-96 w-96 rounded-full bg-purple-600/20 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-5xl px-6 py-20">
        {/* Hero */}
        <div className="text-center animate-fade-in-up">
          <div className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-4 py-1.5 text-xs text-zinc-400 backdrop-blur">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Powered by Google Gemini &amp; Vertex AI
          </div>

          <h1 className="mt-8 text-4xl sm:text-6xl font-bold tracking-tight">
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              CinePilot AI
            </span>
          </h1>
          <p className="mt-5 text-lg sm:text-xl text-zinc-400 max-w-2xl mx-auto">
            Turn a screenplay PDF into a director-ready previsualization package &mdash;
            scenes, characters, storyboards, cinematic prompts, and a full production
            report &mdash; in minutes, not weeks.
          </p>

          <button
            onClick={onSignIn}
            className="mt-10 inline-flex items-center gap-3 rounded-full bg-white text-zinc-900 px-6 py-3 text-sm font-semibold shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 transition-shadow"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Sign in with Google to get started
          </button>
        </div>

        {/* Pipeline showcase */}
        <div className="mt-24">
          <h2 className="text-center text-sm font-medium uppercase tracking-widest text-zinc-500">
            One upload, seven AI agents, one production package
          </h2>
          <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {PIPELINE.map((step, i) => (
              <div
                key={step.name}
                className="animate-fade-in-up rounded-xl border border-zinc-800 bg-zinc-900/60 backdrop-blur p-5 hover:border-zinc-700 transition-colors"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="text-2xl">{step.icon}</div>
                <div className="mt-3 text-sm font-semibold text-zinc-100">
                  {step.name}
                </div>
                <div className="mt-1 text-xs text-zinc-500 leading-relaxed">
                  {step.desc}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Deliverables */}
        <div className="mt-24 grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
          {["Character Sheets", "Storyboard + Shot List", "Cinematic Prompts", "Director Report"].map(
            (item) => (
              <div key={item} className="text-xs sm:text-sm text-zinc-400">
                <div className="mx-auto mb-2 h-px w-8 bg-gradient-to-r from-indigo-500 to-pink-500" />
                {item}
              </div>
            )
          )}
        </div>

        <div className="mt-24 text-center text-xs text-zinc-600">
          CinePilot AI &mdash; AI Pre-Production Studio
        </div>
      </div>
    </div>
  );
}
