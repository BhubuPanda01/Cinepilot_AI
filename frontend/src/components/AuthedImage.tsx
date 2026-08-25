"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/AuthContext";

/**
 * Storyboard frames are served from an authenticated endpoint so one user cannot
 * read another's images. A plain <img src> cannot send an Authorization header,
 * so fetch the bytes and render them from an object URL instead.
 */
export function AuthedImage({
  path,
  alt,
  apiBase,
  className,
}: {
  path: string;
  alt: string;
  apiBase: string;
  className?: string;
}) {
  const { user } = useAuth();
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!user) return;
    let objectUrl: string | null = null;
    let cancelled = false;

    (async () => {
      try {
        const token = await user.getIdToken();
        const res = await fetch(`${apiBase}${path}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(String(res.status));
        const blob = await res.blob();
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [user, path, apiBase]);

  if (failed) {
    return (
      <div className="mt-2 rounded-md border border-zinc-200 dark:border-zinc-800 px-3 py-2 text-xs text-zinc-500">
        Image unavailable
      </div>
    );
  }

  if (!src) {
    return (
      <div className="mt-2 h-40 w-full max-w-sm animate-pulse rounded-md bg-zinc-100 dark:bg-zinc-900" />
    );
  }

  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt={alt} className={className} />;
}
