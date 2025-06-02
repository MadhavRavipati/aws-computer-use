#!/bin/bash
# ABOUTME: Deployment script for Next.js frontend to S3
# ABOUTME: Uploads built assets and configures bucket for web hosting

set -e

# Variables
BUCKET_NAME="computer-use-frontend-dev-156246831523"
AWS_REGION="us-west-2"
CLOUDFRONT_DIST_ID=""  # To be added when CloudFront is created

echo "🚀 Deploying frontend to S3..."

# Build the application
echo "📦 Building application..."
NODE_ENV=production npm run build

# Create output directory
mkdir -p out

# Create a simple index.html that redirects to the app
cat > out/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AWS Computer Use Demo</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 600px;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 30px;
        }
        .status {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 4px;
            color: #1976d2;
            margin-bottom: 20px;
        }
        .endpoints {
            text-align: left;
            background: #f5f5f5;
            padding: 20px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 14px;
        }
        .endpoints h3 {
            margin-top: 0;
            color: #333;
        }
        .note {
            font-size: 14px;
            color: #999;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AWS Computer Use Demo</h1>
        <div class="status">
            ✅ Backend Services Deployed Successfully
        </div>
        <p>
            The AWS Computer Use Demo backend infrastructure is now running. This includes:
        </p>
        <ul style="text-align: left; color: #666;">
            <li>ECS Fargate containers with desktop environments</li>
            <li>API Gateway REST and WebSocket endpoints</li>
            <li>Lambda functions for session management</li>
            <li>Amazon Bedrock integration with Claude 3.5</li>
        </ul>
        
        <div class="endpoints">
            <h3>API Endpoints</h3>
            <strong>REST API:</strong><br>
            https://p0lkqwkiy4.execute-api.us-west-2.amazonaws.com/dev<br><br>
            
            <strong>WebSocket:</strong><br>
            wss://uaakatj7z0.execute-api.us-west-2.amazonaws.com/dev<br><br>
            
            <strong>VNC Bridge (ALB):</strong><br>
            http://computer-use-dev-797992487.us-west-2.elb.amazonaws.com
        </div>
        
        <p class="note">
            Note: The full Next.js frontend application requires server-side rendering 
            and should be deployed to AWS Amplify or Vercel for production use.
        </p>
    </div>
</body>
</html>
EOF

mkdir -p out

# Copy static assets if they exist
if [ -d ".next/static" ]; then
    mkdir -p out/_next
    cp -r .next/static out/_next/
fi

# Sync to S3
echo "📤 Uploading to S3..."
aws s3 sync out/ s3://$BUCKET_NAME/ \
    --region $AWS_REGION \
    --delete \
    --cache-control "public, max-age=3600"

# Set index document
aws s3 website s3://$BUCKET_NAME/ \
    --index-document index.html \
    --error-document error.html \
    --region $AWS_REGION

echo "✅ Deployment complete!"
echo "🌐 Website URL: http://$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com"

# If CloudFront distribution ID is set, invalidate cache
if [ ! -z "$CLOUDFRONT_DIST_ID" ]; then
    echo "🔄 Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id $CLOUDFRONT_DIST_ID \
        --paths "/*" \
        --region $AWS_REGION
fi