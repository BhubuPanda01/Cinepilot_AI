import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Every page is a client component talking to the Cloud Run API, so the app
  // ships as static assets on Firebase Hosting -- no Node server needed.
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
