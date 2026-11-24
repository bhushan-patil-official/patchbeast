import path from "node:path";
import type { NextConfig } from "next";

const standalone = process.env.BUILD_STANDALONE === "1"; // Docker/VPS only; Vercel must NOT set this

const config: NextConfig = {
  ...(standalone
    ? { output: "standalone" as const, outputFileTracingRoot: path.join(__dirname, "../../") }
    : {}),
  transpilePackages: ["@patchbeast/design-system", "@patchbeast/api-client"],
  poweredByHeader: false,
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
      { source: "/feed", headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }] },
    ];
  },
};
export default config;
