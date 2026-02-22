#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1-}" ]; then
  echo "Usage: $0 <GCP_PROJECT_ID> [REGION]"
  exit 1
fi

PROJECT_ID=$1
REGION=${2:-northamerica-northeast1}

echo "🚀 Deploying Voice Scheduling Agent Frontend to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Configure gcloud
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "📌 Enabling Google Cloud APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com --quiet

# Build the frontend
echo "📦 Building frontend..."
npm run build

# Create a Dockerfile for the frontend (self-contained)
cat > Dockerfile <<EOF
FROM nginx:stable-alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOF

# Create nginx config
cat > nginx.conf <<EOF
server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Build Docker image using Cloud Build
echo "🔨 Building Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/voice-frontend --timeout=600s .

# Deploy to Cloud Run
echo "📤 Deploying to Cloud Run..."
gcloud run deploy voice-frontend \
  --image gcr.io/$PROJECT_ID/voice-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080

# Clean up temporary files
rm -f nginx.conf

# Get service URL
FRONTEND_URL=$(gcloud run services describe voice-frontend --platform managed --region $REGION --format='value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "Frontend URL: $FRONTEND_URL"
