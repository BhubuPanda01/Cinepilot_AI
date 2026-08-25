export type ParseProgress = {
  step: number;
  total_steps: number;
  step_name: string;
};

const STEP_ICONS = ["📄", "🎭", "🧑‍🤝‍🧑", "🎬", "✍️", "🔍", "📋"];

export function PipelineProgress({ progress }: { progress: ParseProgress }) {
  const percent = Math.round((progress.step / progress.total_steps) * 100);

  return (
    <div className="w-full rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          {STEP_ICONS[Math.min(progress.step, STEP_ICONS.length - 1)]}{" "}
          {progress.step_name}
        </span>
        <span className="text-sm font-semibold bg-gradient-to-r from-indigo-500 to-pink-500 bg-clip-text text-transparent">
          {percent}%
        </span>
      </div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="mt-2 text-xs text-zinc-400">
        Step {progress.step} of {progress.total_steps} &mdash; this can take a few minutes across
        7 AI agents.
      </div>
    </div>
  );
}
