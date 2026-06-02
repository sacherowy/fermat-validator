# Quickstart: FerMat Validator

**Date**: 2026-06-02

This guide covers setting up, running, and verifying the FerMat Validator after
the domain migration from OMJ Validator.

---

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for `download_fermat.py` — runs outside Docker)
- `GEMINI_API_KEY` available
- Access to the FerMat task PDFs (sp221.edu.pl)

---

## 1. Clone and configure

```bash
git clone <repo-url> fermat-validator
cd fermat-validator

# Copy environment template
cp .env.example .env
# Edit .env: set GEMINI_API_KEY, optionally GOOGLE_CLIENT_ID/SECRET
```

---

## 2. Download task PDFs

```bash
# Download all FerMat PDFs from sp221.edu.pl into tasks/
python download_fermat.py

# Or download a specific edition:
python download_fermat.py --year 2024
```

Expected output:
```
[FerMat] Downloading edition 2024 etap1... OK (tasks.pdf, solutions.pdf)
[FerMat] Downloading edition 2024 etap2... OK (tasks.pdf)
...
[FerMat] Summary: 18 files downloaded, 0 skipped, 0 errors
```

---

## 3. Verify scoring configuration

```bash
cat config/scoring.yml
```

Expected (default):
```yaml
etap1:
  task_groups:
    - tasks: [1, 2, 3, 4, 5]
      max_points: 2
    - tasks: [6, 7, 8, 9, 10]
      max_points: 4
etap2:
  task_groups:
    - tasks: [1, 2, 3, 4, 5]
      max_points: 2
    - tasks: [6, 7, 8, 9, 10]
      max_points: 4
```

---

## 4. Start the application

```bash
# Start all services (PostgreSQL + FastAPI + Next.js)
./start.sh

# Or rebuild images first (after code changes)
./start.sh --build
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Database: localhost:5433

---

## 5. Smoke-test checklist

### ✅ Homepage loads with FerMat branding

Open http://localhost:3000 — verify:
- [ ] Title shows "FerMat Validator" (not "Trener OMJ")
- [ ] No "OMJ" or "Olimpiada Matematyczna Juniorów" text visible to user
- [ ] Footer links point to FerMat resources, not omj.edu.pl

### ✅ Task browsing (User Story 1)

1. Navigate to http://localhost:3000
2. Click any edition (e.g., "Edycja IX — 2025")
3. Select "Etap I"
4. Click Task 1
5. Verify: task content loads, submission form visible

### ✅ AI scoring with solution (User Story 2 — edition 2024/2025 etap I)

1. Navigate to a 2024 Etap I task (e.g., Zadanie 3)
2. Upload any image file as a "solution"
3. Submit
4. Verify response contains:
   - [ ] Score between 0 and 2 (for tasks 1–5) or 0 and 4 (for tasks 6–10)
   - [ ] Polish feedback text
   - [ ] Disclaimer indicating non-official assessment

### ✅ AI scoring without solution (edition pre-2024)

1. Navigate to a 2019 Etap II task
2. Upload and submit a solution
3. Verify response contains:
   - [ ] Message that official solution is unavailable
   - [ ] Score and feedback based on task content only

### ✅ Progressive hints (User Story 3)

1. Navigate to any task with hints configured
2. Click "Pokaż wskazówkę" four times
3. Verify: each click reveals a more specific hint; 5th click shows "all hints revealed"

### ✅ Scoring config hot-reload

1. Edit `config/scoring.yml` — change `etap1 tasks 1–5 max_points` to `3`
2. Submit a new solution for a 2024 etap1 task 1
3. Verify: score is now between 0 and 3 (not 0 and 2)
4. Revert the change

---

## 6. Production deployment

```bash
# Build and push Docker images (from local machine)
./build-and-push.sh

# Deploy to NUC server
./deploy.sh

# Wipe old OMJ data first (run on server):
./deploy.sh --ssh
# On server:
docker compose down -v   # clears old DB
docker compose up -d
```

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| "Brak konfiguracji punktacji" on submit | `config/scoring.yml` missing or invalid | Check file exists; validate YAML syntax |
| AI returns score > max_points | Clamping not applied | Verify `scoring_config.py` is called in `parse_ai_response` |
| OMJ text still visible | Incomplete migration | Search codebase: `grep -ri "omj" frontend/src/` |
| PDF not found for task | `download_fermat.py` not run | Run `python download_fermat.py` |
| Container name still "omj-*" in `docker ps` | Old compose not updated | Pull latest and `docker compose down && docker compose up -d` |
