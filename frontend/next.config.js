/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Emit a minimal self-contained server bundle at .next/standalone —
  // picked up by the Docker runtime stage for a ~200 MB production image.
  output: "standalone",
};

module.exports = nextConfig;
