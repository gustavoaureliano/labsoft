import type { NextConfig } from "next";

const devOrigin = process.env.DEV_ORIGIN;

const nextConfig: NextConfig = {
  allowedDevOrigins: devOrigin ? [devOrigin] : [],
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/:path*` }];
  },
  experimental: {
    useTypeScriptCli: false,
    proxyClientMaxBodySize: "101mb",
  },
};

export default nextConfig;
