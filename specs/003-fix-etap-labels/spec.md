# Feature Specification: Korekta opisów etapów (etap1/etap2)

**Feature Branch**: `003-fix-etap-labels`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "W obecnym podziale na etapy jest wskazanie na etap szkolny i wojewódzki. W przypadku konkursu Fermat nie ma takiego podziału, są dwa etapy szkolne. Popraw opisy w aplikacji oraz w testach E2E (jeśli są)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Poprawne etykiety etapów w nawigacji (Priority: P1)

Użytkownik wchodzi na stronę listy etapów dla danej edycji (np. `/years/2024`) i widzi opisy obu etapów zgodne z rzeczywistą strukturą konkursu FerMat — oba etapy są szkolne.

**Why this priority**: Etap II był błędnie opisany jako "etap wojewódzki" ("Etap wojewódzki" w Next.js i "Etap II (okręgowy)" w szablonach HTML). To wprowadza uczniów w błąd co do charakteru zawodów. Jest to bezpośrednio widoczne dla każdego odwiedzającego stronę.

**Independent Test**: Wejście na `/years/2024` i sprawdzenie, że karta Etapu II nie zawiera słów "wojewódzki", "okręgowy" ani żadnego innego określenia etapu regionalnego.

**Acceptance Scenarios**:

1. **Given** użytkownik jest na stronie `/years/2024`, **When** widzi listę etapów, **Then** opis Etapu I nie zawiera słów "szkolny", "okręgowy", "wojewódzki" w sposób sugerujący inny szczebel niż szkolny
2. **Given** użytkownik jest na stronie `/years/2024`, **When** widzi opis Etapu II, **Then** opis NIE zawiera słów "wojewódzki", "okręgowy", "regionalny" — zamiast tego poprawnie oddaje charakter drugiego etapu szkolnego
3. **Given** użytkownik korzysta z szablonu HTML (`/years/2024/etap2` przez stare routes), **When** widzi nagłówek strony, **Then** nagłówek NIE zawiera "(okręgowy)"

---

### User Story 2 - Spójna terminologia w całej aplikacji (Priority: P2)

Wszystkie miejsca w aplikacji (frontend Next.js, szablony Jinja2 HTML) stosują jednolite, poprawne etykiety etapów FerMat.

**Why this priority**: Niespójne etykiety między nowymi stronami Next.js a starymi szablonami HTML (używanymi np. przez bezpośredni dostęp do backendu) pogłębiają dezorientację.

**Independent Test**: Przeszukanie całej bazy kodu pod kątem słów "okręgowy" i "wojewódzki" — nie powinny występować w kontekście nazewnictwa etapów FerMat.

**Acceptance Scenarios**:

1. **Given** plik `templates/etap.html`, **When** renderowany dla `etap2`, **Then** nagłówek wyświetla "Etap II (szkolny)" zamiast "Etap II (okręgowy)"
2. **Given** plik `templates/year.html`, **When** wyświetla listę etapów, **Then** etap2 jest opisany jako "Etap II (szkolny)" zamiast "Etap II (okręgowy)"
3. **Given** komponent Next.js `years/[year]/page.tsx`, **When** renderuje metadane karty etap2, **Then** `description` nie zawiera "wojewódzki"

---

### User Story 3 - Poprawne filtry na stronie "Moje rozwiązania" (Priority: P2)

Użytkownik korzystający ze strony `/my-solutions` widzi w filtrach tylko etapy i edycje, które faktycznie istnieją w konkursie FerMat.

**Why this priority**: Filtr etapów zawiera opcję "Etap III" której nie ma w FerMat. Filtr lat pokazuje lata od 2005, podczas gdy FerMat startował w 2017 — użytkownik może wybrać rok, dla którego nie istnieją żadne zadania.

**Independent Test**: Wejście na `/my-solutions` i sprawdzenie listy opcji w filtrze etapów (brak "Etap III") oraz filtrze lat (zakres od 2017 do bieżącego roku).

**Acceptance Scenarios**:

1. **Given** użytkownik jest na stronie `/my-solutions`, **When** otwiera filtr "Etap", **Then** dostępne opcje to wyłącznie "Wszystkie", "Etap I" i "Etap II" — brak "Etap III"
2. **Given** użytkownik jest na stronie `/my-solutions`, **When** otwiera filtr "Rok", **Then** lista zaczyna się od roku 2017 (pierwsza edycja FerMat), a nie od 2005
3. **Given** użytkownik jest na stronie `/my-solutions`, **When** otwiera filtr "Rok", **Then** lista kończy się na bieżącym roku (dynamicznie generowana)

---

### Edge Cases

- Jeśli w przyszłości zostanie dodany `etap3`, jego opis musi być osobno zdefiniowany — nie może odziedziczyć błędnego szablonu.
- Zmiany dotyczą wyłącznie etykiet i zakresów wyświetlanych użytkownikowi — klucze URL (`etap1`, `etap2`) i identyfikatory w bazie danych pozostają niezmienione.
- Rok startowy FerMat (2017) powinien być stałą konfiguracyjną, nie zakodowaną wartością — ale zmiana architektury jest poza zakresem tej funkcji; wystarczy zmienić wartość 2005 → 2017.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Opis Etapu II widoczny dla użytkownika NIE MOŻE zawierać słów "wojewódzki", "okręgowy" ani innych określeń szczebla regionalnego.
- **FR-002**: Opis Etapu I i Etapu II MUSI oddawać charakter etapu szkolnego (np. "Etap I (szkolny)", "Etap II (szkolny)").
- **FR-003**: Zmiana MUSI objąć wszystkie miejsca wyświetlające opisy etapów: komponent Next.js `years/[year]/page.tsx`, szablon Jinja2 `templates/etap.html`, szablon Jinja2 `templates/year.html`.
- **FR-004**: Identyfikatory URL i klucze bazy danych (`etap1`, `etap2`) NIE MOGĄ być zmieniane — zmiana dotyczy wyłącznie tekstów widocznych dla użytkownika.
- **FR-005**: Jeśli testy E2E zawierają asercje sprawdzające konkretne etykiety etapów (np. `getByText('Etap II (okręgowy)')`), MUSZĄ zostać zaktualizowane do nowych etykiet.
- **FR-006**: Filtr etapów na stronie `/my-solutions` MUSI zawierać wyłącznie opcje "Etap I" i "Etap II" — opcja "Etap III" MUSI zostać usunięta.
- **FR-007**: Filtr lat na stronie `/my-solutions` MUSI zaczynać się od roku 2017 (pierwsza edycja FerMat), a nie od 2005.

### Key Entities

- **Etykieta etapu**: Wyświetlany tekst opisujący etap zawodów (np. "Etap II (szkolny)"). Niezależna od klucza URL/identyfikatora etapu.
- **Identyfikator etapu**: Klucz URL i bazy danych (`etap1`, `etap2`) — niezmieniony przez tę funkcję.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Żadne miejsce w interfejsie użytkownika (Next.js + szablony HTML) nie wyświetla słów "wojewódzki" ani "okręgowy" w kontekście nazewnictwa etapów FerMat.
- **SC-002**: Oba etapy są konsekwentnie opisane jako szkolne we wszystkich zidentyfikowanych plikach (co najmniej 3 miejsca: `years/[year]/page.tsx`, `templates/etap.html`, `templates/year.html`).
- **SC-003**: Filtr etapów na `/my-solutions` zawiera dokładnie 2 opcje etapów (Etap I, Etap II) — bez Etapu III.
- **SC-004**: Filtr lat na `/my-solutions` zawiera tylko lata 2017–bieżący rok.
- **SC-005**: Istniejące testy E2E dotyczące nawigacji po etapach (w szczególności `tasks.spec.ts`) zaliczają się po wprowadzeniu zmian.
- **SC-006**: Nie ma regresji w żadnym innym teście jednostkowym ani E2E wynikającej z tej zmiany.

## Assumptions

- Właściwy opis dla Etapu II to "Etap II (szkolny)" — analogicznie do Etapu I który jest już poprawnie opisany w szablonie jako "Etap I (szkolny)".
- W testach E2E (`e2e/tests/tasks.spec.ts`) sprawdzane są etykiety `Etap I` i `Etap II` bez szczegółowych opisów (np. "(szkolny)") — dlatego zmiana opisów nie wymagają modyfikacji tych testów, chyba że zostaną znalezione asercje na pełny tekst z opisem.
- Zmiany są czysto prezentacyjne — nie wpływają na logikę oceniania, routing, bazy danych ani integrację AI.
- Stary frontend HTML (Jinja2) jest nadal używany (np. `/years`, `/task/...` przez bezpośredni dostęp do backendu na porcie 8000), więc wymaga aktualizacji.
