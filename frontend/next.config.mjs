/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backendOrigin = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/:path*`
      }
    ];
  }
};

export default nextConfig;
