import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

const devOrigin = process.env.DEV_ORIGIN;

const nextConfig: NextConfig = {
  allowedDevOrigins: devOrigin ? [devOrigin] : [],
  async rewrites() {
    const learning = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
    const identity = process.env.IDENTITY_URL ?? "http://127.0.0.1:18101";
    return [
      { source: "/api/v1/:path*", destination: `${identity}/api/v1/:path*` },
      { source: "/api/:path*", destination: `${learning}/api/:path*` },
    ];
  },
  turbopack: {
    root: frontendRoot,
  },
  experimental: {
    useTypeScriptCli: false,
    proxyClientMaxBodySize: "101mb",
  },
};

export default nextConfig;
