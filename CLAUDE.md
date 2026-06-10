# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FerMat Validator — a web application for validating solutions to the FerMat mathematical competition run by SP221 school (https://sp221.edu.pl/fermat/). Students upload photos of their handwritten solutions, which are analyzed by AI (Gemini) against official task PDFs and scoring criteria.

**Architecture**: Monorepo with Next.js frontend and FastAPI backend, deployed as separate services.

## Important Rules

**NEVER discard uncommitted changes without explicit user permission.** Do not run commands like `git checkout <file>`, `git restore <file>`, or `git reset --hard` on files with uncommitted changes unless the user explicitly asks you to discard those changes. Always ask first if you see uncommitted changes that seem unrelated to the current task.

## Development Commands

```bash
# Start full development environment (PostgreSQL + backend + frontend via Docker)
./start.sh

# Start only backend (PostgreSQL + FastAPI on port 8000)
./start.sh --backend-only

# Start only frontend (Next.js on port 3000, requires backend running)
./start.sh --frontend-only

# Force rebuild of Docker images
./start.sh --build

# Stop all services
docker compose down

# Stop and delete all data (including database)
docker compose down -v

# View logs
docker compose logs -f            # All services
docker compose logs -f api        # Backend only
docker compose logs -f frontend   # Frontend only

# Download task PDFs from sp221.edu.pl (run outside Docker)
python download_fermat.py                      # All editions
python download_fermat.py --year 2024          # Specific year
python download_fermat.py --dry-run            # List without downloading

# Update task content with LaTeX from PDFs (uses Claude CLI)
python fix_latex_content.py 2024 etap1        # Specific year/etap
python fix_latex_content.py --all             # All tasks

# Generate/update task metadata (difficulty, categories, hints)
python populate_metadata.py                    # Uses Claude CLI
python populate_metadata.py --year 2024 --force

# Populate task prerequisites
python populate_prerequisites.py

# Generate task index
python generate_task_index.py

# Review/update hints
python review_hints.py

# Create task JSON files from scratch
python create_tasks.py

# Migrate tasks (data transformation scripts)
python scripts/migrate_tasks.py

# Run E2E tests (requires Docker)
cd e2e && ./run-e2e.sh

# --- Unit tests ---

# Backend unit tests (run outside Docker, from repo root)
pip install -r requirements-dev.txt   # pytest, pytest-asyncio
pytest tests/                          # All backend tests
pytest tests/unit/test_parsing.py     # Single file

# Frontend unit tests (from frontend/)
cd frontend && npm test                # Run once (vitest)
cd frontend && npm run test:watch      # Watch mode
```

**Note**: Development uses Docker Compose for the full stack. Google OAuth is disabled by default (`AUTH_DISABLED=true`) since it requires an external URL for callbacks.

## Architecture

### Project Structure

```
fermat-validator/
├── frontend/                # Next.js 16 frontend (TypeScript, React 19)
│   ├── src/
│   │   ├── app/            # Next.js App Router pages
│   │   ├── components/     # React components
│   │   └── lib/            # API client, hooks, types, utils
│   ├── next.config.ts      # API proxy rewrites to FastAPI
│   └── package.json
├── app/                     # FastAPI backend (Python)
│   ├── main.py             # Routes (HTML + JSON APIs)
│   ├── config.py           # Pydantic settings
│   ├── auth.py             # Session-based auth helpers
│   ├── oauth.py            # Google OAuth (Authlib)
│   ├── groups.py           # Access control (email allowlist or Google Groups)
│   ├── storage.py          # Task loading (dir scan + LRU cache)
│   ├── models.py           # Pydantic models
│   ├── progress.py         # Task progression graph logic
│   ├── skills.py           # Skills data loader (data/skills.json)
│   ├── db/                 # Database layer
│   │   ├── session.py      # SQLAlchemy engine, get_db dependency
│   │   ├── models.py       # ORM: UserDB, SubmissionDB
│   │   └── repositories.py # Data access layer
│   ├── ai/
│   │   ├── protocol.py     # AIProvider interface
│   │   ├── factory.py      # Provider factory
│   │   ├── parsing.py      # JSON parsing, score normalization
│   │   ├── prompt_builder.py  # Builds Gemini prompt from scoring config + task
│   │   ├── scoring_config.py  # Loads config/scoring.yml
│   │   └── providers/
│   │       └── gemini.py   # Gemini API integration
│   ├── translate/           # Google Cloud Translation (EN→PL status messages)
│   │   └── client.py
│   └── websocket/           # Real-time submission progress via WebSocket
│       ├── handler.py      # Background AI processing + WS message dispatch
│       ├── messages.py     # WebSocket message types
│       └── progress.py     # In-memory progress state manager
├── config/
│   └── scoring.yml          # Scoring rules per etap (max points per task group)
├── data/                    # Runtime data
│   ├── tasks/              # Task metadata JSON files
│   ├── uploads/            # User-submitted images
│   └── skills.json         # Skills taxonomy
├── tasks/                   # Downloaded task PDFs (by year/etap)
├── alembic/                # Database migrations
├── prompts/                # AI prompts for analysis
│   ├── gemini_prompt_base.txt        # Base system prompt
│   ├── gemini_prompt_scoring_etap1.txt
│   ├── gemini_prompt_scoring_etap2.txt
│   └── gemini_prompt_abuse.txt       # Abuse/injection detection prompt
├── e2e/                     # Playwright end-to-end tests
│   ├── tests/              # Test specs
│   ├── fake-gemini/        # Fake Gemini API server for E2E
│   ├── fake-translate/     # Fake Translation API server for E2E
│   └── run-e2e.sh          # E2E test runner
├── tests/                   # Backend unit tests (pytest)
│   └── unit/
├── templates/               # Jinja2 HTML templates (legacy HTML routes)
├── static/                  # Static assets for legacy HTML routes
├── docker-compose.yml      # Development Docker Compose (full stack)
├── docker-compose.prod.yml # Production Docker Compose
├── docker-compose.e2e.yml  # E2E test Docker Compose
├── Dockerfile              # Production backend Dockerfile
├── Dockerfile.dev          # Development backend Dockerfile (hot-reload)
└── start.sh                # Development startup script
```

### Frontend (Next.js)

**Tech stack**: Next.js 16, React 19, TypeScript, Material-UI v7, Tailwind CSS v4, KaTeX, Cytoscape.js, SWR, Vitest

**Key directories**:
```
frontend/src/
├── app/                              # App Router pages
│   ├── layout.tsx                    # Root layout with MUI ThemeProvider
│   ├── years/page.tsx               # List all editions
│   ├── years/[year]/page.tsx        # List etaps for edition
│   ├── years/[year]/[etap]/page.tsx # Task list for etap
│   ├── task/[year]/[etap]/[num]/page.tsx  # Task detail with submission
│   ├── progress/page.tsx            # Task progression graph
│   ├── my-solutions/page.tsx        # User's submission history & stats
│   ├── practice/etap2/page.tsx      # Etap2 practice mode with timer
│   ├── admin/submissions/page.tsx   # Admin panel (admin users only)
│   ├── regulamin/page.tsx           # Terms of service
│   └── login/page.tsx               # Google OAuth login
├── components/
│   ├── layout/                      # Header, Footer, Breadcrumb, PageHeader
│   ├── task/                        # TaskCard, SubmitSection, HintsSection, SkillsSection, SubmissionHistory
│   ├── progress/                    # ProgressGraph, CategoryFilter, ProgressStats, RecommendationsList, Etap2PrepList
│   ├── my-solutions/                # MySolutionsDashboard, SubmissionCard, StatisticsCards, FiltersBar
│   ├── practice/                    # MockEtap2Section, PracticeTimer, FloatingTimer
│   ├── admin/                       # AdminSubmissionsTable, UserAutocomplete
│   ├── auth/                        # LoginForm
│   ├── common/                      # LoginPrompt
│   ├── providers/                   # ThemeProvider
│   └── ui/                          # DifficultyStars, CategoryBadge, MathContent
└── lib/
    ├── api/client.ts                # Fetch helpers (client-side)
    ├── api/server.ts                # Fetch helpers (server-side)
    ├── contexts/TimerContext.tsx    # Practice timer state
    ├── hooks/useAuth.ts             # Auth state hook
    ├── hooks/useInfiniteScroll.ts   # Infinite scroll hook
    ├── utils/constants.ts           # App-wide constants
    ├── utils/dates.ts               # Date formatting
    ├── utils/formatTime.ts          # Time formatting
    └── types/index.ts               # TypeScript types (match FastAPI models)
```

**API proxy**: `next.config.ts` rewrites `/api/*`, `/auth/*`, `/login/*`, `/logout`, `/pdf/*`, `/uploads/*`, `/ws/*` to FastAPI backend.

### Backend (FastAPI)

**HTML routes** (legacy Jinja2, used directly via browser):
```
GET  /years                          # List all editions
GET  /years/{year}                   # List etaps for year
GET  /years/{year}/{etap}            # Task list for etap
GET  /task/{year}/{etap}/{num}       # Task detail
GET  /task/{year}/{etap}/{num}/history  # Submission history (HTML)
GET  /progress                       # Task progression graph (HTML)
GET  /auth/limited                   # Limited access page
GET  /login                          # Login page
GET  /login/google                   # Google OAuth redirect
GET  /auth/callback                  # OAuth callback
GET  /logout                         # Logout
```

**JSON API routes** (used by Next.js frontend):
```
GET  /api/auth/me                    # Current user info
GET  /api/years                      # All editions
GET  /api/years/{year}               # Etaps for year
GET  /api/years/{year}/{etap}        # Tasks for etap
GET  /api/task/{year}/{etap}/{num}   # Task detail
GET  /api/task/{year}/{etap}/{num}/history  # Submission history
GET  /api/progress/data              # Task progression data
GET  /api/my-submissions             # Current user's submissions (paginated)
GET  /api/sitemap-data               # Task identifiers for sitemap
GET  /api/admin/submissions          # All submissions (admin only)
GET  /api/admin/users/search         # User search autocomplete (admin only)
GET  /api/admin/me                   # Admin status check
POST /task/{year}/{etap}/{num}/submit       # Submit solution (returns submission_id)
WS   /ws/submissions/{submission_id}        # WebSocket for real-time progress
```

**Static routes**:
```
GET  /pdf/{year}/{etap}/{filename}   # Serve task PDFs
GET  /uploads/{path}                 # Serve uploaded images (auth required)
GET  /health                         # Health check
```

**E2E test endpoints** (only when `E2E_MODE=true`):
```
POST /api/test/reset-user-submissions
POST /api/test/reset-all-submissions
```

### Database (PostgreSQL)

**Tables**:
- `users` - Google OAuth users (google_sub PK, email, name, created_at)
- `submissions` - Solution submissions (user_id FK, year, etap, task_number, score, feedback, status, issue_type, abuse_score)

**Local**: PostgreSQL 16 via Docker on port 5433 (`postgresql://fermat:fermat@localhost:5433/fermat`)

**Migrations**: Alembic in `alembic/versions/`
- `001_initial_schema.py`
- `002_add_users_created_at_index.py`
- `003_add_abuse_detection.py`

### Key Data Flows

1. **Task Loading**: Per-task JSON files at `data/tasks/{year}/{etap}/task_{num}.json`. Scanned on startup and cached.

   Task JSON structure:
   ```json
   {
     "number": 1,
     "title": "Task title with $LaTeX$",
     "content": "Full task content with $LaTeX$ notation",
     "pdf": {"tasks": "...", "solutions": "...", "statistics": "..."},
     "difficulty": 3,
     "categories": ["geometria", "algebra"],
     "hints": ["hint1", "hint2", "hint3", "hint4"],
     "prerequisites": ["2023_etap1_2"],
     "skills_required": ["skill_id_1"],
     "skills_gained": ["skill_id_2"]
   }
   ```

   Valid categories: `algebra`, `geometria`, `teoria_liczb`, `kombinatoryka`, `logika`, `arytmetyka`

2. **Submission Flow** (async with WebSocket progress):
   - `POST /task/{year}/{etap}/{num}/submit` — images saved, DB record created (`PENDING`), returns `submission_id`
   - Client connects to `WS /ws/submissions/{submission_id}` for real-time updates
   - Background task processes images via Gemini AI, updates DB to `PROCESSING` → `COMPLETED`/`FAILED`
   - WebSocket pushes progress events to client

3. **FerMat Scoring** (from `config/scoring.yml`):
   - **Etap1**: Tasks 1–5 → max 2 pts, Tasks 6–10 → max 4 pts
   - **Etap2**: Tasks 1–5 → max 4 pts
   - No etap3 for FerMat (unlike OMJ)

4. **AI Integration**: Uses Gemini File API. Prompts are split by etap in `prompts/`. Abuse detection runs a separate prompt to flag wrong-task submissions and injection attempts.

5. **Skills System**: `data/skills.json` defines a taxonomy of mathematical skills. Tasks declare `skills_required` and `skills_gained`. Displayed on task detail pages.

6. **LaTeX Rendering**: Frontend uses KaTeX via `MathContent` component.

7. **Abuse Detection**: Every submission is checked for prompt injection (`IssueType.INJECTION`) and wrong-task submissions (`IssueType.WRONG_TASK`). Results stored in `submissions.issue_type` and `submissions.abuse_score`.

### Configuration

**Backend environment variables** (`.env`):

```bash
# Authentication (disabled by default for local dev)
AUTH_DISABLED=true
SESSION_SECRET_KEY=dev-secret-key-change-in-production

# Google OAuth (optional for local dev, required for production)
# GOOGLE_CLIENT_ID=...
# GOOGLE_CLIENT_SECRET=...

# Access control
# PUBLIC_ACCESS=true  # Allow all authenticated users to submit (with rate limits)
# ALLOWED_EMAILS=user1@gmail.com,user2@example.com  # Rate limit bypass
# OR (when PUBLIC_ACCESS=false, only these users get full access)
# GOOGLE_GROUP_EMAIL=your-group@googlegroups.com
# GOOGLE_SERVICE_ACCOUNT_JSON={...}

# Admin users (comma-separated)
# ADMIN_EMAILS=admin@gmail.com

# AI
AI_PROVIDER=gemini
GEMINI_API_KEY=...                        # Required
GEMINI_MODEL=gemini-3-pro-preview         # Default model
GEMINI_TIMEOUT=90
GEMINI_THINKING_LEVEL=low                 # "low" (fast) or "high" (thorough)
GEMINI_MEDIA_RESOLUTION=high              # PDF resolution: "low", "medium", "high"
GEMINI_MEDIA_RESOLUTION_IMAGES=ultra_high # Student image resolution (Gemini 3 only)
GEMINI_DISABLE_FILE_CACHE=false           # Force fresh PDF upload each request
GEMINI_DEBUG_LOGS=false

# Translation (EN→PL for status messages, optional)
# TRANSLATE_ENABLED=true
# TRANSLATE_API_KEY=...
# TRANSLATE_TIMEOUT=2.0

# Rate limiting (rolling 24h)
# RATE_LIMIT_NEW_USERS_PER_DAY=50
# RATE_LIMIT_SUBMISSIONS_PER_USER_PER_DAY=30
# RATE_LIMIT_SUBMISSIONS_GLOBAL_PER_DAY=500

# Note: DATABASE_URL is set in docker-compose.yml for container networking
```

**Frontend environment**: Set in `docker-compose.yml` (`FASTAPI_URL=http://api:8000`).

## Deployment

### Local Development

```bash
./start.sh  # Starts all services via Docker Compose
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Database: localhost:5433

All services run in Docker with hot-reload enabled. Code changes in `app/` and `frontend/src/` are automatically picked up.

### Production (NUC Server)

Deployed on a local Intel NUC server with Docker Compose and Cloudflare Tunnel.

**Deployment workflow** (build locally, pull on server):
```bash
# One-time setup: login to GitHub Container Registry
# 1. Create PAT at https://github.com/settings/tokens with 'write:packages' scope
# 2. Login: echo YOUR_PAT | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Build and push images from local machine
./build-and-push.sh

# Deploy to server (pulls images from ghcr.io)
./deploy.sh

# Or build and deploy in one command
./build-and-push.sh && ./deploy.sh
```

**Useful commands**:
```bash
./deploy.sh --status        # Check container status
./deploy.sh --logs api      # View API logs
./deploy.sh --ssh           # SSH into server
```

See **[docs/production-deployment.md](docs/production-deployment.md)** for complete setup guide, operations, and troubleshooting.

## Testing

### Backend unit tests (pytest)

Located in `tests/unit/`. Run directly from the repo root (no Docker needed):

```bash
pip install -r requirements-dev.txt   # pytest>=8.0, pytest-asyncio>=0.23
pytest tests/
```

| File | What it covers |
|---|---|
| `test_parsing.py` | `app/ai/parsing.py` — JSON extraction, score clamping, abuse-detection response parsing |
| `test_scoring_config.py` | `app/ai/scoring_config.py` — YAML config loading, `get_max_points()` per etap/task |
| `test_auth.py` | `app/auth.py` — session helpers, auth verification |
| `test_progress.py` | `app/progress.py` — progression graph logic, prerequisite resolution |
| `test_repositories.py` | `app/db/repositories.py` — `ensure_utc`, stale-submission detection; uses in-memory SQLite |

`tests/conftest.py` adds the repo root to `sys.path` so `import app.*` works without installation.

### Frontend unit tests (Vitest)

Located alongside source in `frontend/src/lib/utils/__tests__/`. Run from `frontend/`:

```bash
npm test          # Run once
npm run test:watch  # Watch mode
```

| File | What it covers |
|---|---|
| `constants.test.ts` | App-wide constants |
| `dates.test.ts` | Date formatting utilities |
| `formatTime.test.ts` | Timer/time formatting utilities |

Test setup file: `frontend/src/test/setup.ts` (imports `@testing-library/jest-dom`).

### E2E tests (Playwright)

Located in `e2e/tests/`. Requires Docker — uses fake Gemini and Translation API servers.

```bash
cd e2e && ./run-e2e.sh
```

Key test specs: `auth`, `submission`, `navigation`, `tasks`, `progress`, `my-solutions`, `rate-limiting`, `websocket`, `admin`.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at `specs/002-fermat-task-download/plan.md`.
<!-- SPECKIT END -->
