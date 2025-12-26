import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // Turbopack is enabled by default in dev with --turbopack flag
  // This gives Vite-like fast refresh experience
  
  // Strict mode for better development experience
  reactStrictMode: true,

  // Image optimization settings
  images: {
    domains: [],
    unoptimized: process.env.NODE_ENV === "development",
  },
};

export default nextConfig;
