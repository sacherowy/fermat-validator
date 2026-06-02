# Implementation Plan: FerMat Validator — Domain Migration from OMJ

**Branch**: `001-fermat-validator-app` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-fermat-validator-app/spec.md`

## Summary

Migrate the existing OMJ Validator web application to FerMat Validator — a training
tool for students preparing for the FerMat Mathematical Competition organized by
SP 221 Warsaw. The migration changes the domain and data (competition name, task
sources, scoring logic) while preserving the full technology stack and architecture.
Core deliverable: a YAML-driven scoring system replacing hardcoded OMJ score sets,
plus full removal of OMJ branding across ~26 files.

## Technical Context

**Language/Version**: Python 3.11 (FastAPI backend) / TypeScript (Next.js 16, React 19 frontend)

**Primary Dependencies**: FastAPI, SQLAlchemy 2, Alembic, google-genai, PyYAML (new),
Next.js 16, Material-UI v7, SWR, KaTeX, Cytoscape.js

**Storage**: PostgreSQL 16 (Docker), filesystem (`tasks/` for PDFs, `data/uploads/`
for student images, `config/` for scoring YAML)

**Testing**: pytest (backend); no test framework change needed — existing test suite
covers submission and parsing logic

**Target Platform**: Linux server via Docker Compose; web browser (desktop + mobile)

**Project Type**: Fullstack web-service (monorepo: `app/` + `frontend/`)

**Performance Goals**: AI scoring ≤2 min at p95 (inherited from spec SC-002); no
new performance requirements introduced

**Constraints**:
- No architectural refactoring (Constitution II) — existing layers preserved
- All OMJ symbol references removed from code (Constitution I, FR-011)
- Scoring MUST be YAML-driven, not hardcoded (Constitution III)
- `etap3` removed throughout (FerMat has only etap1/etap2)
- DB schema unchanged; old data cleared via `docker compose down -v` before deploy

**Scale/Scope**: ~500 students max, single NUC server, ~9 editions × 2 etaps × 10 tasks
= ~180 tasks total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Domain Fidelity | No OMJ identifiers in any user-facing surface after migration (FR-011) | ✅ PASS — FR-011 mandates full removal; tracked in Phase 2–4 |
| II. Architecture Continuity | No new layers, patterns, or framework introductions | ✅ PASS — PyYAML is a single-file utility dep; no new architectural pattern |
| III. Configurable Scoring | `config/scoring.yml` loaded at runtime; no hardcoded score values remain | ✅ PASS — `scoring_config.py` loader designed in Phase 1 |
| IV. Educational Intent | Every score response includes non-official disclaimer | ✅ PASS — FR-005 already in spec; disclaimer in prompt template |
| V. Data Availability Awareness | Graceful fallback when no solution PDF (all editions except 2024–2025 etap1) | ✅ PASS — existing logic in `gemini.py` `has_solution_pdf` check preserved |

No violations → Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-fermat-validator-app/
├── plan.md              # This file
├── research.md          # Phase 0 — decisions and rationale
├── data-model.md        # Phase 1 — entities and YAML schema
├── quickstart.md        # Phase 1 — how to run + verify
├── contracts/
│   └── scoring-config.md  # YAML scoring contract (admin-facing)
└── tasks.md             # Phase 2 — /speckit-tasks output (not yet created)
```

### Source Code Changes (repository root)

```text
# Changed files (no new directories except config/)
app/
├── ai/
│   ├── parsing.py            # normalize_omj_score() → normalize_fermat_score(score, max_points)
│   │                         # Remove VALID_SCORES_ETAP* constants
│   ├── prompt_builder.py     # Remove etap3 entry; build_prompt(etap, task_number, max_points)
│   ├── scoring_config.py     # NEW: YAML loader — get_max_points(etap, task_number)
│   └── providers/
│       └── gemini.py         # RESPONSE_JSON_SCHEMA description; pass max_points to prompt
├── db/
│   ├── __init__.py           # Docstring: OMJ → FerMat
│   ├── models.py             # Docstring: OMJ → FerMat
│   ├── repositories.py       # Docstring: OMJ → FerMat
│   └── session.py            # Docstring: OMJ → FerMat
├── config.py                 # Default group email; DB URL comment
├── main.py                   # FastAPI title "FerMat Validator"
├── models.py                 # Docstring; category taxonomy comment
├── progress.py               # Docstring
└── skills.py                 # Docstring

config/                       # NEW directory
└── scoring.yml               # FerMat scoring scale (admin-editable)

prompts/
├── gemini_prompt_scoring_etap1.txt  # Replaced: FerMat etap1 criteria (0-2 pts)
├── gemini_prompt_scoring_etap2.txt  # Replaced: FerMat etap2 criteria (0-4 pts)
└── gemini_prompt_scoring_etap3.txt  # DELETED (FerMat has no etap3)

frontend/src/
├── app/
│   ├── layout.tsx                        # keywords, description, JSON-LD
│   ├── page.tsx                          # homepage copy
│   ├── opengraph-image.tsx               # OG branding
│   ├── sitemap.ts                        # SITE_URL
│   ├── robots.ts                         # SITE_URL
│   ├── regulamin/page.tsx                # Full rewrite: OMJ → FerMat
│   ├── years/page.tsx                    # Title, description
│   ├── years/[year]/page.tsx             # Title, description
│   ├── years/[year]/[etap]/page.tsx      # Title, description
│   ├── task/[year]/[etap]/[num]/page.tsx # Title
│   ├── progress/page.tsx                 # Description
│   └── practice/etap2/page.tsx          # Description
├── components/layout/
│   ├── Footer.tsx                        # Links, description
│   └── PageHeader.tsx                    # Comment (minor)
└── lib/
    ├── utils/constants.ts                # APP_NAME, APP_TITLE, SITE_URL, CONTACT_EMAIL
    └── contexts/TimerContext.tsx         # localStorage key "omj-practice-timer"

docker-compose.e2e.yml        # Container names, DB name (omj_e2e → fermat_e2e)

download_fermat.py            # NEW: CLI script — downloads PDFs from sp221.edu.pl
```

## Complexity Tracking

> No constitution violations detected — section not applicable.
