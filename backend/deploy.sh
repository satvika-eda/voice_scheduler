#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1-}" ]; then
  echo "Usage: $0 <GCP_PROJECT_ID> [REGION]"
  echo "Example: $0 my-project us-central1"
  exit 1
fi

PROJECT_ID=$1
REGION=${2:-us-central1}

echo "🚀 Deploying Voice Scheduling Agent Backend to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Load environment variables from root .env (API keys) and local .env (config)
if [ -f "../.env" ]; then
  echo "📋 Loading API keys from ../.env..."
  export $(cat ../.env | grep -v '^#' | grep -v '^$' | xargs)
fi

if [ -f ".env" ]; then
  echo "📋 Loading config from .env..."
  export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

# Check required env vars
if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "⚠️  OPENAI_API_KEY not found in .env files"
  exit 1
fi

# Set default values for optional env vars
GOOGLE_CALENDAR_ID=${GOOGLE_CALENDAR_ID:-primary}
CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000,http://localhost:5173,http://localhost:5174}
DEFAULT_TIMEZONE=${DEFAULT_TIMEZONE:-America/New_York}

# Configure gcloud
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "📌 Enabling Google Cloud APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com --quiet

# Build and push Docker image using Cloud Build
echo "🔨 Building Docker image..."
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/voice-backend \
  --timeout=1800s \
  .

# Deploy to Cloud Run with environment variables
echo "📤 Deploying to Cloud Run..."

# Build the env vars string with proper escaping for commas in CORS_ORIGINS
gcloud run deploy voice-backend \
  --image gcr.io/$PROJECT_ID/voice-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars "^||^OPENAI_API_KEY=$OPENAI_API_KEY||GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID||GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET||GOOGLE_CALENDAR_ID=$GOOGLE_CALENDAR_ID||CORS_ORIGINS=$CORS_ORIGINS||DEFAULT_TIMEZONE=$DEFAULT_TIMEZONE"

# Print service URL
BACKEND_URL=$(gcloud run services describe voice-backend --platform managed --region $REGION --format='value(status.url)')
echo ""
echo "✅ Deployment complete!"
echo "Backend URL: $BACKEND_URL"
echo ""
echo "📝 Update GOOGLE_REDIRECT_URI if needed:"
echo "  Current value: $GOOGLE_REDIRECT_URI"
echo "  New value (recommended): $BACKEND_URL/auth/callback"
