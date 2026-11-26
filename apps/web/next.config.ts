import path from "node:path";
import type { NextConfig } from "next";

const standalone = process.env.BUILD_STANDALONE === "1"; // Docker/VPS only; Vercel must NOT set this

const config: NextConfig = {
  ...(standalone
    ? { output: "standalone" as const, outputFileTracingRoot: path.join(__dirname, "../../") }
    : {}),
  transpilePackages: ["@patchbeast/design-system", "@patchbeast/api-client"],
  poweredByHeader: false,
  // Put <title>/<meta description>/canonical in the initial <head> for EVERY crawler. By default Next streams
  // metadata into <body> for user agents it does not recognise as bots (Bing, social scrapers, AI crawlers...).
  htmlLimitedBots: /.*/,
  experimental: { inlineCss: true }, // inline the (small) CSS: removes a render-blocking request
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
