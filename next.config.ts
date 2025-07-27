import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
};

export default nextConfig;
