import os
import ssl

# Disable SSL verification globally BEFORE any other imports that use requests/urllib3
# Required for corporate proxy environments that intercept HTTPS
from app.config import get_settings as _get_settings
_s = _get_settings()
if _s.HF_DISABLE_SSL.lower() in ("1", "true", "yes"):
    os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"
    os.environ["CURL_CA_BUNDLE"] = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["TRANSFORMERS_OFFLINE"] = "0"
    ssl._create_default_https_context = ssl._create_unverified_context

    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Monkey-patch requests.Session to force verify=False on ALL requests
    import requests
    _original_request = requests.Session.request

    def _patched_request(self, *args, **kwargs):
        kwargs.setdefault("verify", False)
        return _original_request(self, *args, **kwargs)

    requests.Session.request = _patched_request

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.api import auth, chat, files, models as models_api, knowledge

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and upload directory
    init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    yield


app = FastAPI(title="Generative AI Chat", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chats", tags=["chats"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(models_api.router, prefix="/api/models", tags=["models"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
