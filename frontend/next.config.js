/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: false,
  devIndicators: false,
  // Loyiha ildizini aniq ko'rsatamiz — yuqori papkadagi boshqa lockfile bilan aralashmasin
  outputFileTracingRoot: path.join(__dirname),
  images: {
    unoptimized: true
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/static/:path*',
        destination: 'http://127.0.0.1:8000/static/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
