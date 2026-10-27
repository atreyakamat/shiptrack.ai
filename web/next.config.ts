import type { NextConfig } from "next";

const BACKEND = process.env.BACKEND_URL ?? "http://127.0.0.1:5000";

const nextConfig: NextConfig = {
  // Human-assisted India Post lookups wait for the user to solve a CAPTCHA (up to ~90s).
  experimental: { proxyTimeout: 120_000 },
  // Proxy API calls to Flask so the browser stays same-origin (no CORS needed).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND}/api/:path*` }];
  },
};

export default nextConfig;
