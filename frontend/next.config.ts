import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

const devOrigin = process.env.DEV_ORIGIN;

// Prototype microservices (see docker-compose.yml). Override hosts with env vars if needed.
const services = {
  access: process.env.ACCESS_URL ?? "http://localhost:8001",
  checkout: process.env.CHECKOUT_URL ?? "http://localhost:8002",
  subscription: process.env.SUBSCRIPTION_URL ?? "http://localhost:8003",
  payment: process.env.PAYMENT_URL ?? "http://localhost:8004",
  metering: process.env.METERING_URL ?? "http://localhost:8005",
};

const nextConfig: NextConfig = {
  allowedDevOrigins: devOrigin ? [devOrigin] : [],
  async rewrites() {
    const learning = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
    const identity = process.env.IDENTITY_URL ?? "http://127.0.0.1:18101";
    return [
      { source: "/api/v1/:path*", destination: `${identity}/api/v1/:path*` },
      { source: "/api/access", destination: `${services.access}/api/access` },
      { source: "/api/checkout/:path*", destination: `${services.checkout}/api/checkout/:path*` },
      { source: "/api/subscriptions/:path*", destination: `${services.subscription}/api/subscriptions/:path*` },
      { source: "/api/payments/:path*", destination: `${services.payment}/api/payments/:path*` },
      { source: "/api/heartbeat", destination: `${services.metering}/api/heartbeat` },
      { source: "/api/usage/:path*", destination: `${services.metering}/api/usage/:path*` },
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
