import type { NextConfig } from "next";

type NextConfigWithTurbopack = NextConfig & {
  turbopack?: {
    root: string
  }
}

const nextConfig: NextConfigWithTurbopack = {
  // In Cursor/sandbox environments Next.js may infer a workspace root that
  // points outside the allowed filesystem. Pin Turbopack's root to this app.
  turbopack: {
    root: __dirname,
  },
  /* config options here */
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
      },
    ]
  },
};

export default nextConfig;
