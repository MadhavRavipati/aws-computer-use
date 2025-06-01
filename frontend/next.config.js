// ABOUTME: Next.js configuration for Computer Use frontend
// ABOUTME: Configures build settings, environment variables, and optimizations

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typescript: {
    // Strict type checking
    tsconfigPath: './tsconfig.json',
  },
  eslint: {
    // Run ESLint on these directories during build
    dirs: ['app', 'components', 'lib', 'hooks'],
  },
  images: {
    // Configure image optimization
    domains: ['localhost', 's3.amazonaws.com'],
    formats: ['image/avif', 'image/webp'],
  },
  env: {
    // Runtime environment variables
    NEXT_PUBLIC_API_ENDPOINT: process.env.NEXT_PUBLIC_API_ENDPOINT,
    NEXT_PUBLIC_WS_ENDPOINT: process.env.NEXT_PUBLIC_WS_ENDPOINT,
  },
  async headers() {
    return [
      {
        // Security headers
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  webpack: (config) => {
    // Custom webpack configuration
    config.module.rules.push({
      test: /\.worker\.js$/,
      use: { loader: 'worker-loader' },
    });
    return config;
  },
};

module.exports = nextConfig;