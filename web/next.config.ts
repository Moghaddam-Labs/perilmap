import type { NextConfig } from "next";
import { staticSecurityHeaders } from "./src/lib/security";

const config: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  headers: async () => [{ source: "/:path*", headers: staticSecurityHeaders }],
};

export default config;
