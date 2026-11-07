import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));

const devOrigin = process.env.DEV_ORIGIN;

// Internal HTTP destinations. No credential translation happens in these rewrites.
const services = {
  access: process.env.ACCESS_URL ?? "http://127.0.0.1:18105",
  checkout: process.env.CHECKOUT_URL ?? "http://127.0.0.1:18107",
  subscription: process.env.SUBSCRIPTION_URL ?? "http://127.0.0.1:18104",
  payment: process.env.PAYMENT_URL ?? "http://127.0.0.1:18108",
  metering: process.env.METERING_URL ?? "http://127.0.0.1:18109",
};

const nextConfig: NextConfig = {
  allowedDevOrigins: devOrigin ? [devOrigin] : [],
  async rewrites() {
    const learning = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
    const identity = process.env.IDENTITY_URL ?? "http://127.0.0.1:18101";
    const catalog = process.env.CATALOG_URL ?? "http://127.0.0.1:18103";
    const engagement = process.env.ENGAGEMENT_URL ?? "http://127.0.0.1:18106";
    return [
      { source: "/api/v1/:path*", destination: `${identity}/api/v1/:path*` },
      { source: "/api/media/:id/download", destination: `${catalog}/api/media/:id/download` },
      ...["courses", "teacher/courses", "landing", "search", "recommendations"].map(path => ({
        source: `/api/${path}/:path*`, destination: `${catalog}/api/${path}/:path*`,
      })),
      ...["library", "interactions", "questions", "notifications", "moderation", "analytics"].map(path => ({
        source: `/api/${path}/:path*`, destination: `${engagement}/api/${path}/:path*`,
      })),
      { source: "/api/access", destination: `${services.access}/api/access` },
      { source: "/api/subscriptions/:path*", destination: `${services.subscription}/api/subscriptions/:path*` },
      ...(process.env.NEXT_PUBLIC_AUTH_ENABLED === "true" ? [] : [
        { source: "/api/checkout/:path*", destination: `${services.checkout}/api/checkout/:path*` },
        { source: "/api/payments/:path*", destination: `${services.payment}/api/payments/:path*` },
        { source: "/api/heartbeat", destination: `${services.metering}/api/heartbeat` },
        { source: "/api/usage/:path*", destination: `${services.metering}/api/usage/:path*` },
      ]),
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
