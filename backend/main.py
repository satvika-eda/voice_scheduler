import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from urllib.parse import urlencode

app = FastAPI(
    title="Voice Scheduling Agent API",
    description="Real-time voice scheduling assistant with Google Calendar integration",
    version="1.0.0"
)

# Configure CORS for frontend
ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://localhost:5174').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Import after middleware setup
from api.routes import router as api_router
from utils.logger import log_info, log_error

# Global error handler
@app.middleware('http')
async def log_requests(request: Request, call_next):
    log_info(f'{request.method} {request.url.path}')
    try:
        return await call_next(request)
    except Exception as e:
        log_error(f'Unhandled error: {str(e)}')
        return JSONResponse(
            status_code=500,
            content={'detail': 'Internal server error'}
        )

app.include_router(api_router)

@app.get('/')
async def root():
    return {'message': 'Voice Scheduling Agent API running'}

@app.get('/oauth/callback')
async def oauth_callback(code: str = None, state: str = None, error: str = None):
    """Google OAuth callback handler that returns an HTML page with the auth code."""
    if error:
        return HTMLResponse(f"""
        <html>
            <body style="font-family: sans-serif; padding: 50px; text-align: center;">
                <h1>Authentication Failed</h1>
                <p>Error: {error}</p>
                <p>You can close this window.</p>
                <script>
                    window.close();
                </script>
            </body>
        </html>
        """, status_code=400)
    
    if not code:
        return HTMLResponse("""
        <html>
            <body style="font-family: sans-serif; padding: 50px; text-align: center;">
                <h1>Authentication Failed</h1>
                <p>No authorization code received.</p>
                <p>You can close this window.</p>
                <script>
                    window.close();
                </script>
            </body>
        </html>
        """, status_code=400)
    
    return HTMLResponse(f"""
    <html>
        <body style="font-family: sans-serif; padding: 50px; text-align: center;">
            <h1>✓ Authentication Successful</h1>
            <p>Your Google Calendar is now connected.</p>
            <p>You can close this window and return to the app.</p>
            <script>
                // Extract sessionId from localStorage or URL
                const code = "{code}";
                window.opener.postMessage({{ type: "google_auth_code", code: code }}, "*");
                setTimeout(() => window.close(), 2000);
            </script>
        </body>
    </html>
    """)

