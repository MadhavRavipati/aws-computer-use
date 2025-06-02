#!/bin/bash
# ABOUTME: Simple deployment script for HTML frontend to S3/CloudFront
# ABOUTME: Deploys the standalone HTML application

set -e

BUCKET_NAME="computer-use-frontend-dev-156246831523"
AWS_REGION="us-west-2"
CLOUDFRONT_ID="E1HPHA357GOQKW"

echo "🚀 Deploying simple frontend to S3..."

# Upload the app.html as index.html
echo "📤 Uploading application..."
aws s3 cp public/app.html s3://$BUCKET_NAME/index.html \
    --region $AWS_REGION \
    --content-type "text/html" \
    --cache-control "public, max-age=3600"

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_ID \
    --paths "/*" \
    --region $AWS_REGION \
    --output json > /dev/null

echo "✅ Deployment complete!"
echo "🌐 CloudFront URL: https://d2inxmm0s7bfbg.cloudfront.net"
echo ""
echo "The full interactive application is now available with:"
echo "- Session creation and management"
echo "- VNC desktop viewer"
echo "- AI chat interface"
echo "- Real-time WebSocket communication"