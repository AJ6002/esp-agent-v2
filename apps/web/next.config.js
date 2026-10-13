/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Anchor tracing root to the app directory itself: ensure standalone output is pinned to
  // .next/standalone/server.js (relied upon by Dockerfile and CI startup scripts),
  // while preventing extraneous lockfiles outside the repo from interfering with workspace root inference.
  outputFileTracingRoot: __dirname,
  async rewrites() {
    const apiBase = process.env.API_BASE_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
