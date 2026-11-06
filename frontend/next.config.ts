import type { NextConfig } from "next";

// Prototype microservices (see docker-compose.yml). Override hosts with env vars if needed.
const services = {
  access: process.env.ACCESS_URL ?? "http://localhost:8001",
  checkout: process.env.CHECKOUT_URL ?? "http://localhost:8002",
  subscription: process.env.SUBSCRIPTION_URL ?? "http://localhost:8003",
  payment: process.env.PAYMENT_URL ?? "http://localhost:8004",
  metering: process.env.METERING_URL ?? "http://localhost:8005",
  content: process.env.CONTENT_URL ?? "http://localhost:8006", // mock of the media team's service
};

const nextConfig: NextConfig = {
  experimental: {
    useTypeScriptCli: false,
  },
  async rewrites() {
    return [
      { source: "/api/access", destination: `${services.access}/api/access` },
      { source: "/api/checkout/:path*", destination: `${services.checkout}/api/checkout/:path*` },
      { source: "/api/checkout", destination: `${services.checkout}/api/checkout` },
      { source: "/api/subscriptions/:path*", destination: `${services.subscription}/api/subscriptions/:path*` },
      { source: "/api/subscriptions", destination: `${services.subscription}/api/subscriptions` },
      { source: "/api/payments/:path*", destination: `${services.payment}/api/payments/:path*` },
      { source: "/api/heartbeat", destination: `${services.metering}/api/heartbeat` },
      { source: "/api/learning/lessons/:id/playback", destination: `${services.content}/api/learning/lessons/:id/playback` },
      { source: "/api/documents/:id", destination: `${services.content}/api/documents/:id` },
      { source: "/api/usage/:path*", destination: `${services.metering}/api/usage/:path*` },
    ];
  },
};

export default nextConfig;
