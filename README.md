# Voice Scheduling Agent

A voice-powered meeting scheduler that uses Vapi AI for voice interaction and Google Calendar for event creation.

## Live Demo

**Demo Video:** https://www.loom.com/share/465193776c4a424facda3c6448b5152f

**Frontend:** https://voice-frontend-n5gsv6o6eq-nn.a.run.app

**Backend API:** https://voice-backend-n5gsv6o6eq-nn.a.run.app

### How to Test

1. Open the frontend URL in Chrome
2. Click the microphone button to start a conversation
4. The agent will ask clarifying questions about duration, title, etc.
5. Confirm the details when prompted
6. The event will be created in Google Calendar


## Features

- **Voice-first interface** - Schedule meetings by talking naturally
- **Google Calendar integration** - Events created directly in your calendar
- **AI-powered** - Uses OpenAI for natural language understanding
- **Cloud-ready** - Deploy to Google Cloud Run

---

## Calendar Integration

### How It Works

The calendar integration uses a **Google Cloud Service Account** for server-to-server authentication. This approach eliminates the need for users to go through OAuth flows.

**Flow:**
1. User speaks meeting details (name, date, time, duration, title)
2. Vapi AI extracts structured data via tool calls
3. Frontend sends event data to backend API
4. Backend uses service account credentials to authenticate with Google Calendar API
5. Event is created in the configured calendar
6. Calendar invite is sent to the specified attendee email

**Key components:**

- [backend/calendar_providers/auth.py](backend/calendar_providers/auth.py) - Handles service account authentication
- [backend/calendar_providers/google_calendar.py](backend/calendar_providers/google_calendar.py) - Creates calendar events
- [backend/api/routes.py](backend/api/routes.py) - API endpoint `/api/calendar/create`

**Service Account Setup:**
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Share your Google Calendar with the service account email (grant "Make changes to events" permission)
4. The service account can now create events on your behalf

**Why Service Account over OAuth?**
- No user login required - simpler UX for voice-first interaction
- Server-side authentication - more secure, credentials never exposed to client
- Works for demo/single-calendar use cases
- OAuth flow is also supported for multi-user scenarios

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│   Google    │
│   (React)   │     │  (FastAPI)  │     │  Calendar   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│    Vapi     │     │   OpenAI    │
│  Voice AI   │     │     API     │
└─────────────┘     └─────────────┘
```

---

## Run Locally (Optional)

### Prerequisites

- Node.js 18+
- Python 3.11+
- Google Cloud account
- Vapi account
- OpenAI API key

### 1. Clone and Setup

```bash
git clone https://github.com/satvika-eda/voice_scheduler.git
cd voice_scheduling_agent

# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Configure Environment Variables

Edit `.env` with your API keys:
- `OPENAI_API_KEY` - From OpenAI dashboard
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - From Google Cloud Console
- `VAPI_PUBLIC_KEY` - From Vapi dashboard

Edit `backend/.env`:
- `GOOGLE_CALENDAR_ID` - Your Google Calendar email
- `CORS_ORIGINS` - Allowed frontend URLs

Edit `frontend/.env`:
- `VITE_BACKEND_URL` - Backend API URL
- `VITE_VAPI_PUBLIC_KEY` - Vapi public key

### 3. Setup Google Calendar

1. Create a service account in Google Cloud Console
2. Download the JSON key and save as `backend/service_account.json`
3. Share your Google Calendar with the service account email

### 4. Run Locally

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Deployment Guide

### Prerequisites for Deployment

1. **Google Cloud CLI** installed and authenticated
   ```bash
   gcloud auth login
   gcloud config set project <PROJECT_ID>
   ```

2. **Enable required GCP APIs**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable calendar-json.googleapis.com
   ```

3. **Create Google Cloud credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create OAuth 2.0 Client ID (Web application)
   - Add authorized redirect URI: `https://<BACKEND_URL>/auth/callback`
   - Download and note the Client ID and Secret

4. **Create Service Account for Calendar**
   - Go to IAM & Admin → Service Accounts
   - Create new service account
   - Download JSON key → save as `backend/service_account.json`
   - Share your Google Calendar with the service account email (give "Make changes to events" permission)

5. **Get Vapi credentials**
   - Sign up at [vapi.ai](https://vapi.ai)
   - Get your Public Key from the dashboard
   - Create an assistant and note the Assistant ID

### Step 1: Configure Environment Variables

Create `.env` files with your credentials:

**Root `.env`:**
```bash
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
VAPI_PUBLIC_KEY=...
VAPI_ASSISTANT_ID=...
```

**`backend/.env`:**
```bash
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
GOOGLE_CALENDAR_ID=your-email@gmail.com
CORS_ORIGINS=http://localhost:5173,https://voice-frontend-xxx.a.run.app
```

**`frontend/.env`:**
```bash
VITE_BACKEND_URL=https://voice-backend-xxx.a.run.app
VITE_VAPI_PUBLIC_KEY=...
VITE_VAPI_ASSISTANT_ID=...
```

### Step 2: Deploy Backend

```bash
cd backend
bash deploy.sh <PROJECT_ID> <REGION>

# Example:
bash deploy.sh vigilant-card-488100-q1 northamerica-northeast1
```

The script will:
- Build Docker image
- Push to Google Container Registry
- Deploy to Cloud Run with environment variables
- Output the backend URL

**Note the backend URL** (e.g., `https://voice-backend-n5gsv6o6eq-nn.a.run.app`)

### Step 3: Update OAuth Redirect URI

After getting the backend URL:
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Edit your OAuth 2.0 Client ID
3. Add authorized redirect URI: `https://<BACKEND_URL>/auth/callback`

### Step 4: Update Frontend Environment

Update `frontend/.env` with the deployed backend URL:
```bash
VITE_BACKEND_URL=https://voice-backend-xxx.a.run.app
```

### Step 5: Deploy Frontend

```bash
cd frontend
bash deploy.sh <PROJECT_ID> <REGION>

# Example:
bash deploy.sh vigilant-card-488100-q1 northamerica-northeast1
```

### Step 6: Update Backend CORS

After frontend is deployed, update backend CORS to include frontend URL:

1. Edit `backend/.env`:
   ```bash
   CORS_ORIGINS=http://localhost:5173,https://voice-frontend-xxx.a.run.app
   ```

2. Redeploy backend:
   ```bash
   cd backend
   bash deploy.sh <PROJECT_ID> <REGION>
   ```

### Step 7: Configure Vapi Assistant

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai)
2. Create or edit your assistant
3. Add the server tool with your backend URL:
   - Tool name: `collect_meeting_details`
   - Server URL: `https://<BACKEND_URL>/api/calendar/create`
4. Update the assistant prompt (see `vapi_config/agent_prompt.txt`)

### Verify Deployment

```bash
# Test backend health
curl https://<BACKEND_URL>/health

# Test session creation
curl -X POST https://<BACKEND_URL>/api/voice/init

# Open frontend
open https://<FRONTEND_URL>
```

### Useful Commands

```bash
# View backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=voice-backend" --limit 50

# Redeploy after changes
cd backend && bash deploy.sh <PROJECT_ID> <REGION>
cd frontend && bash deploy.sh <PROJECT_ID> <REGION>

# View service details
gcloud run services describe voice-backend --region <REGION>
gcloud run services describe voice-frontend --region <REGION>
```

---

## Project Structure

```
voice_scheduling_agent/
├── backend/
│   ├── api/routes.py              # API endpoints
│   ├── calendar_providers/
│   │   ├── auth.py                # Service account authentication
│   │   └── google_calendar.py     # Calendar event creation
│   ├── utils/                     # Helpers (datetime, text parsing)
│   ├── main.py                    # FastAPI app entry point
│   ├── deploy.sh                  # Cloud Run deployment script
│   └── tests/                     # API and calendar tests
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── VoiceAgent.jsx     # Main voice UI component
│   │   └── services/api.js        # Backend API client
│   ├── deploy.sh                  # Cloud Run deployment script
│   └── vite.config.js             # Vite configuration
├── vapi_config/                   # Vapi assistant configuration
└── docs/                          # Architecture documentation
```

## Tech Stack

- **Frontend:** React + Vite + Vapi Web SDK
- **Backend:** Python + FastAPI + Uvicorn
- **Voice AI:** Vapi.ai
- **LLM:** OpenAI GPT-3.5-turbo
- **Calendar:** Google Calendar API
- **Deployment:** Google Cloud Run
