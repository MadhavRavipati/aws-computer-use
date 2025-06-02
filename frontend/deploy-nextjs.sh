#!/bin/bash

# ABOUTME: Deployment script for Next.js frontend to S3/CloudFront
# ABOUTME: Builds and deploys the full application with proper assets

set -e

BUCKET_NAME="computer-use-frontend-dev-156246831523"
AWS_REGION="us-west-2"
CLOUDFRONT_ID="E1HPHA357GOQKW"

echo "🚀 Deploying Next.js frontend to S3..."

# Build the application
echo "📦 Building application..."
npm run build

# Check if out directory exists
if [ ! -d "out" ]; then
    echo "❌ Build failed: 'out' directory not found"
    echo "Make sure next.config.js has output: 'export'"
    exit 1
fi

# Sync to S3
echo "📤 Uploading to S3..."
aws s3 sync out/ s3://$BUCKET_NAME/ \
    --region $AWS_REGION \
    --delete \
    --cache-control "public, max-age=3600"

# Set proper content types
aws s3 cp s3://$BUCKET_NAME/ s3://$BUCKET_NAME/ \
    --exclude "*" \
    --include "*.html" \
    --recursive \
    --metadata-directive REPLACE \
    --content-type "text/html" \
    --cache-control "public, max-age=3600"

aws s3 cp s3://$BUCKET_NAME/ s3://$BUCKET_NAME/ \
    --exclude "*" \
    --include "*.js" \
    --recursive \
    --metadata-directive REPLACE \
    --content-type "application/javascript" \
    --cache-control "public, max-age=31536000"

aws s3 cp s3://$BUCKET_NAME/ s3://$BUCKET_NAME/ \
    --exclude "*" \
    --include "*.css" \
    --recursive \
    --metadata-directive REPLACE \
    --content-type "text/css" \
    --cache-control "public, max-age=31536000"

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_ID \
    --paths "/*" \
    --region $AWS_REGION

echo "✅ Deployment complete!"
echo "🌐 CloudFront URL: https://d2inxmm0s7bfbg.cloudfront.net"