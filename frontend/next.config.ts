import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

const devOrigin = process.env.DEV_ORIGIN;

const nextConfig: NextConfig = {
  allowedDevOrigins: devOrigin ? [devOrigin] : [],
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/:path*` }];
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
