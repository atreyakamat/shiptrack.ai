import type { NextConfig } from "next";

const BACKEND = process.env.BACKEND_URL ?? "http://127.0.0.1:5000";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle for a small Docker image.
  output: "standalone",
  // Pin the trace root to web/ (build always runs from here) so standalone output isn't
  // nested under the repo root, which still has the old Vite package.json.
  outputFileTracingRoot: process.cwd(),
  // Human-assisted India Post lookups wait for the user to solve a CAPTCHA (up to ~90s).
  experimental: { proxyTimeout: 120_000 },
  // Proxy API calls to Flask so the browser stays same-origin (no CORS needed).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND}/api/:path*` }];
  },
};

export default nextConfig;
