# Implementation Plan: Korekta opisów etapów (etap1/etap2)

**Branch**: `003-fix-etap-labels` | **Date**: 2026-06-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-fix-etap-labels/spec.md`

## Summary

Korekta etykiet etapów w interfejsie użytkownika: zmiana "Etap II (okręgowy)" / "Etap wojewódzki" na "Etap II (szkolny)" / "Drugi etap szkolny" we wszystkich miejscach widocznych dla użytkownika (Next.js + szablony Jinja2). Usunięcie opcji "Etap III" z filtra na stronie `/my-solutions` oraz korekta zakresu lat filtra z 2005→bieżący na 2017→bieżący. Zmiany czysto prezentacyjne — bez modyfikacji routingu, bazy danych, logiki AI ani testów E2E.

## Technical Context

**Language/Version**: Python 3.x, TypeScript / Next.js 16, React 19

**Primary Dependencies**: FastAPI (backend), Next.js App Router (frontend), Jinja2 (HTML templates), Material-UI v7

**Storage**: N/A (no data model changes)

**Testing**: pytest (backend), Vitest (frontend), Playwright E2E — brak asercji na poprawiane etykiety, więc testy nie wymagają zmian

**Target Platform**: Web (Linux server Docker + przeglądarka)

**Project Type**: Web application (monorepo: FastAPI backend + Next.js frontend)

**Performance Goals**: N/A (text-only changes)

**Constraints**: Klucze URL (`etap1`, `etap2`) i identyfikatory DB pozostają bez zmian

**Scale/Scope**: 5 miejsc w kodzie; 0 zmian schematu DB; 0 zmian API

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Domain Fidelity** | ✅ PASS | Ta zmiana **realizuje** zasadę: usuwa terminologię OMJ ("okręgowy", "wojewódzki") zastępując ją poprawną terminologią FerMat ("szkolny") |
| **II. Architecture Continuity** | ✅ PASS | Tylko zmiany UI copy — bez refaktoryzacji architektury |
| **III. Configurable Scoring** | ✅ PASS | Brak zmian w logice scoringu |
| **IV. Educational Intent** | ✅ PASS | Brak zmian w komunikatach AI ani ocenianiu |
| **V. Data Availability Awareness** | ✅ PASS | Brak zmian w obsłudze PDF ani fallback logice |

**Post-design re-check**: Wszystkie zasady nadal spełnione — zmiany są wyłącznie prezentacyjne.

## Phase 0: Research

**Wynik**: Brak nieznanych elementów (NEEDS CLARIFICATION). Wszystkie miejsca wymagające zmian zidentyfikowane przez grep. Nie generuje się research.md — nie ma czego badać.

**Znalezione miejsca wymagające zmian** (pełny wynik analizy kodu):

| Plik | Linia | Obecna wartość | Nowa wartość |
|------|-------|----------------|--------------|
| `frontend/src/app/years/[year]/page.tsx` | 54 | `"Etap wojewódzki"` | `"Drugi etap szkolny"` |
| `templates/year.html` | 24 | `Etap II (okręgowy)` | `Etap II (szkolny)` |
| `templates/etap.html` | 17 | `Etap II (okręgowy)` | `Etap II (szkolny)` |
| `frontend/src/components/my-solutions/FiltersBar.tsx` | 25–27 | `currentYear - 2004` (→ od 2005) | `currentYear - 2016` (→ od 2017) |
| `frontend/src/components/my-solutions/FiltersBar.tsx` | 98 | `<MenuItem value="etap3">Etap III</MenuItem>` | *(usuń)* |

**E2E testy**: grep nie znalazł asercji na "okręgowy", "wojewódzki" ani "Etap III" w `e2e/tests/` — testy E2E nie wymagają zmian.

**Frontend unit testy**: `constants.test.ts` testuje `getMaxScore("etap3")` i `getMasteryThreshold("etap3")` — to wewnętrzne identyfikatory, nie etykiety UI. Nie wymagają zmian.

## Phase 1: Design

### Source Code Layout

```text
# Pliki do modyfikacji (zmiany tekstowe)
frontend/
└── src/
    ├── app/years/[year]/page.tsx          # line 54: description etap2
    └── components/my-solutions/
        └── FiltersBar.tsx                 # lines 25-27 (year range), line 98 (etap3)

templates/
├── year.html                              # line 24: etap2 label
└── etap.html                             # line 17: etap2 heading

specs/003-fix-etap-labels/
├── plan.md          # Ten plik
└── tasks.md         # Phase 2 output (/speckit-tasks command)
```

**Structure Decision**: Option 2 (Web application). Brak nowych plików — wyłącznie modyfikacje istniejących.

### Data Model

Brak zmian schematu danych. Żadne encje nie są modyfikowane. `data-model.md` nie jest generowany.

### API Contracts

Brak zmian API. Endpointy, sygnatury, payloady — bez zmian. `contracts/` nie jest generowany.

### Quickstart

Brak nowych konfiguracji ani kroków setup. `quickstart.md` nie jest generowany.

### Szczegółowy opis zmian

#### 1. `frontend/src/app/years/[year]/page.tsx` — linia 54

```diff
-    description: "Etap wojewódzki",
+    description: "Drugi etap szkolny",
```

Cel: karta Etapu II na stronie `/years/{year}` nie może sugerować szczebla regionalnego.

#### 2. `templates/year.html` — linia 24

```diff
-            Etap II (okręgowy)
+            Etap II (szkolny)
```

Cel: lista etapów w starym widoku HTML.

#### 3. `templates/etap.html` — linia 17

```diff
-    <h1>{{ year }} - {% if etap == "etap1" %}Etap I (szkolny){% elif etap == "etap2" %}Etap II (okręgowy){% elif etap == "etap3" %}Finał{% else %}{{ etap }}{% endif %}</h1>
+    <h1>{{ year }} - {% if etap == "etap1" %}Etap I (szkolny){% elif etap == "etap2" %}Etap II (szkolny){% elif etap == "etap3" %}Finał{% else %}{{ etap }}{% endif %}</h1>
```

Cel: nagłówek strony listy zadań etap2.

#### 4. `frontend/src/components/my-solutions/FiltersBar.tsx` — linie 25–27

```diff
-// Generate year options (current year down to 2005)
+// Generate year options (current year down to 2017, first FerMat edition)
 const currentYear = new Date().getFullYear();
-const YEARS = Array.from({ length: currentYear - 2004 }, (_, i) => (currentYear - i).toString());
+const YEARS = Array.from({ length: currentYear - 2016 }, (_, i) => (currentYear - i).toString());
```

Cel: filtr lat zawiera tylko lata 2017–bieżący rok.

#### 5. `frontend/src/components/my-solutions/FiltersBar.tsx` — linia 98

```diff
-            <MenuItem value="etap3">Etap III</MenuItem>
```

Cel: filtr etapów zawiera tylko Etap I i Etap II.

## Complexity Tracking

*(Brak naruszeń zasad konstytucji — sekcja pusta.)*

## Project Structure

### Documentation (this feature)

```text
specs/003-fix-etap-labels/
├── plan.md              # Ten plik (/speckit-plan output)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

*(research.md, data-model.md, quickstart.md, contracts/ — nie generowane, brak potrzeby)*
