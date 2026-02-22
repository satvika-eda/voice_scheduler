#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1-}" ]; then
  echo "Usage: $0 <GCP_PROJECT_ID> [REGION]"
  exit 1
fi

PROJECT_ID=$1
REGION=$2

# Configure gcloud
gcloud config set project "$PROJECT_ID"

# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com artifactregistry.googleapis.com --quiet

# Build and push images using Cloud Build
echo "Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/voice-backend -f backend/Dockerfile .
echo "Pushing image to Container Registry..."
docker push gcr.io/$PROJECT_ID/voice-backend

# gcloud builds submit --tag gcr.io/$PROJECT_ID/voice-frontend --timeout=1200s .

# Deploy to Cloud Run
gcloud run deploy voice-backend \
  --image gcr.io/$PROJECT_ID/voice-backend \
  --platform managed --region $REGION --allow-unauthenticated --port 8080

# gcloud run deploy voice-frontend \
#   --image gcr.io/$PROJECT_ID/voice-frontend \
#   --platform managed --region $REGION --allow-unauthenticated --port 8080

# Print service URLs
echo "Backend URL: $(gcloud run services describe voice-backend --platform managed --region $REGION --format='value(status.url)')"
# echo "Frontend URL: $(gcloud run services describe voice-frontend --platform managed --region $REGION --format='value(status.url)')"
