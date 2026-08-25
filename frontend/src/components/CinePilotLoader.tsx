export function CinePilotLoader({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="relative h-16 w-16">
        <svg
          viewBox="0 0 48 48"
          className="h-16 w-16 animate-spin-slow"
          style={{ animationDuration: "3s" }}
        >
          <circle
            cx="24"
            cy="24"
            r="20"
            fill="none"
            stroke="url(#cp-gradient)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray="70 55"
          />
          <defs>
            <linearGradient id="cp-gradient" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="50%" stopColor="#c084fc" />
              <stop offset="100%" stopColor="#f472b6" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-[10px] font-semibold tracking-wider text-indigo-500 dark:text-indigo-300">
            CP
          </span>
        </div>
      </div>
      <div className="text-center">
        <div className="text-sm font-semibold tracking-wide bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
          CinePilot AI
        </div>
        {label && <div className="mt-1 text-xs text-zinc-500">{label}</div>}
      </div>
    </div>
  );
}
