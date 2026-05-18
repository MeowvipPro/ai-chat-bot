# Generative AI Chat

A full-stack AI chat application with support for multiple AI providers, file upload with Q&A, and a modern dark/light mode UI.

## Features

- **Chat with AI** — Send messages and receive streamed responses (SSE)
- **Multiple AI Providers** — OpenAI, HuggingFace (offline), and AWS Bedrock (Claude)
- **Model Selection** — Switch between models mid-conversation
- **File Upload & Q&A** — Upload PDFs, text files, and images; ask questions about their content using RAG
- **Authentication** — JWT-based login/signup with auto-refresh
- **Chat History** — All conversations saved and loadable from sidebar
- **Multi-Database** — SQLite (default), MySQL, or MSSQL via `DB_TYPE` in `.env`
- **Configurable Embeddings** — Local (SentenceTransformer) or AWS Bedrock Titan
- **Dark/Light Mode** — Theme toggle with localStorage persistence

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, Alembic |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4 |
| Database | SQLite (default), MySQL, MSSQL |
| AI | OpenAI SDK, HuggingFace Transformers, AWS Bedrock (boto3) |
| Vector Store | ChromaDB + sentence-transformers / Bedrock Titan Embeddings |
| File Processing | pdfplumber, pytesseract (OCR), Pillow |
| Auth | JWT (python-jose), bcrypt |
| Streaming | Server-Sent Events (SSE) |
| State | Zustand |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) MySQL 8.0 or MSSQL if not using SQLite
- (Optional) Tesseract OCR for image-based file uploads

### 1. Clone & configure

```bash
cd GenerativeAIChat
```

Edit `backend/.env` with your settings. Key options:

```env
# Database — choose one: sqlite | mysql | mssql
DB_TYPE=sqlite
SQLITE_PATH=./app.db

# AI Providers (configure whichever you use)
OPENAI_API_KEY=your-key
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_SESSION_TOKEN=your-token
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# Embedding model: all-MiniLM-L6-v2 | all-mpnet-base-v2 | amazon.titan-embed-text-v1
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 2. Run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

> **Windows:** If you have multiple Python versions, use the full path:
> ```powershell
> & "C:\path\to\python.exe" -m pip install -r requirements.txt
> & "C:\path\to\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
> ```

The API will be available at http://127.0.0.1:8000. Tables are created automatically on first startup.

### 3. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173. Vite proxies `/api` requests to the backend.

## Run locally on Windows (no Docker)

One-time setup:

```powershell
# Backend deps
cd backend
pip install -r requirements.txt
Copy-Item .env.example .env   # then edit .env with your API keys

# Frontend deps
cd ..\frontend
npm install
```

Then from the repo root, start both servers in two windows:

```powershell
.\start.ps1
```

Open http://localhost:5173 in your browser. The frontend dev server proxies `/api` to the backend on port 8000, so nothing else needs configuring.

If PowerShell blocks the script with an execution-policy error, run it once with:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

To stop, just close the two spawned PowerShell windows.

## Deploying without Docker

The included `render.yaml` is **Docker-free**: backend runs on Render's native Python runtime, frontend ships as a Render Static Site. To deploy:

1. Push this repo to GitHub.
2. In the Render dashboard → **New → Blueprint** → point at this repo.
3. Render reads `render.yaml` and creates two services:
   - `ai-chat-bot-backend` (Python) — `pip install -r requirements.txt` then `uvicorn app.main:app`
   - `ai-chat-bot-frontend` (Static) — `npm ci && npm run build`, serves `dist/`
4. In the backend service settings, fill in `OPENAI_API_KEY` / `GEMINI_API_KEY` / `AWS_*` secrets (they're declared with `sync: false` so Render won't sync them automatically).
5. The frontend gets `VITE_API_BASE_URL` injected at build time pointing at the backend; the backend gets `FRONTEND_URL` for CORS.

That's it — no Dockerfiles, no nginx, no compose.

### Other hosts (any VPS / Fly / Railway / etc.)

Same idea, just run the two processes:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (build static assets, then serve dist/ with any static server)
cd frontend
VITE_API_BASE_URL=https://your-backend.example.com npm run build
npx serve dist  # or upload dist/ to Netlify / Vercel / S3 / Cloudflare Pages
```

Set `FRONTEND_URL` on the backend to the frontend's public URL (used for CORS).

### Docker Compose (optional, if you prefer containers)

```bash
docker compose up --build
```

Opens frontend at http://localhost:5173 and API at http://localhost:8000.

## Project Structure

```
GenerativeAIChat/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (AI providers, auth, files, vector store)
│   │   ├── utils/        # Helpers (chunking, embeddings)
│   │   ├── config.py     # Settings from .env
│   │   ├── database.py   # SQLAlchemy engine & session
│   │   ├── dependencies.py # FastAPI dependencies (auth)
│   │   └── main.py       # App entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/   # React UI components
│   │   ├── context/      # Auth context provider
│   │   ├── hooks/        # useChat (Zustand store), useTheme
│   │   ├── pages/        # Login, Signup, Dashboard
│   │   ├── services/     # API client, auth helpers
│   │   └── styles/       # Tailwind CSS
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login, get JWT tokens |
| POST | `/api/auth/refresh-token` | Refresh access token |
| GET | `/api/auth/me` | Get current user |
| GET | `/api/chats/` | List user's chats |
| POST | `/api/chats/` | Create new chat |
| GET | `/api/chats/{id}` | Get chat with messages |
| PUT | `/api/chats/{id}` | Update chat title/model |
| DELETE | `/api/chats/{id}` | Delete chat |
| POST | `/api/chats/{id}/messages` | Send message (SSE stream) |
| POST | `/api/files/upload` | Upload file |
| GET | `/api/files/` | List uploaded files |
| POST | `/api/files/{id}/qa` | Ask question about file |
| DELETE | `/api/files/{id}` | Delete file |
| GET | `/api/models/available` | List available AI models |
