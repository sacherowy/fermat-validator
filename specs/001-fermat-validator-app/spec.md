# Feature Specification: FerMat Validator — Aplikacja treningowa

**Feature Branch**: `001-fermat-validator-app`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "Aplikacja pomaga uczniom klas 4–6 przygotować się do Konkursu
Matematycznego FerMat organizowanego przez SP 221 w Warszawie."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Przeglądanie zadań (Priority: P1)

Uczeń wchodzi na stronę i widzi listę edycji konkursu FerMat (I–IX, lata 2017–2025).
Wybiera edycję i etap (I lub II), po czym widzi listę zadań z tej edycji.
Klika w zadanie i widzi jego treść wraz z ewentualnymi wskazówkami.

**Why this priority**: To fundament aplikacji — bez możliwości przeglądania zadań
żadna inna funkcja nie ma sensu.

**Independent Test**: Można w pełni przetestować otwierając stronę główną i
nawigując do dowolnego zadania bez logowania ani przesyłania czegokolwiek.

**Acceptance Scenarios**:

1. **Given** uczeń otwiera stronę główną, **When** wyświetla się lista edycji,
   **Then** widzi dziewięć edycji (I–IX, 2017–2025) z podziałem na etapy.
2. **Given** uczeń wybiera edycję i etap, **When** klika na edycję/etap,
   **Then** widzi listę zadań przypisanych do tej edycji i etapu.
3. **Given** uczeń wybiera konkretne zadanie, **When** otwiera stronę zadania,
   **Then** widzi pełną treść zadania (tekst, ewentualne rysunki) oraz możliwość
   przesłania rozwiązania.

---

### User Story 2 — Przesyłanie rozwiązania i ocena AI (Priority: P2)

Uczeń na stronie zadania przesyła zdjęcie lub skan swojego odręcznego rozwiązania.
System ocenia rozwiązanie przy pomocy AI (Gemini) na podstawie treści zadania
(PDF), oficjalnego rozwiązania (jeśli dostępne) i skonfigurowanej skali punktowej.
Uczeń otrzymuje punkty oraz pisemne uzasadnienie w języku polskim.

**Why this priority**: To główna wartość edukacyjna aplikacji — natychmiastowa
informacja zwrotna o jakości rozwiązania.

**Independent Test**: Można przetestować przesyłając dowolne zdjęcie do zadania
z edycji 2024 etap I (gdzie dostępne jest oficjalne rozwiązanie) i weryfikując,
czy ocena i uzasadnienie są zwrócone w języku polskim w ciągu 2 minut.

**Acceptance Scenarios**:

1. **Given** uczeń jest na stronie zadania, **When** przesyła plik (JPG/PNG/PDF)
   ze swoim rozwiązaniem, **Then** system akceptuje plik i wyświetla komunikat
   o trwającej analizie.
2. **Given** zadanie pochodzi z edycji 2024 lub 2025 etap I,
   **When** AI analizuje rozwiązanie, **Then** ocena uwzględnia porównanie
   z oficjalnym rozwiązaniem i skonfigurowaną skalą punktową.
3. **Given** zadanie pochodzi z edycji innej niż 2024/2025 etap I,
   **When** AI analizuje rozwiązanie, **Then** system informuje ucznia, że
   oficjalne rozwiązanie nie jest dostępne, i ocena opiera się wyłącznie
   na treści zadania.
4. **Given** analiza AI zakończy się pomyślnie, **When** wynik jest gotowy,
   **Then** uczeń widzi: liczbę punktów, pisemne uzasadnienie w języku polskim
   oraz komunikat wskazujący na nieoficjalny charakter oceny.
5. **Given** uczeń przesłał wcześniej rozwiązanie, **When** ponownie odwiedza
   stronę zadania, **Then** widzi historię swoich poprzednich prób z wynikami.

---

### User Story 3 — Progresywne wskazówki (Priority: P3)

Uczeń, który nie wie jak podejść do zadania, może poprosić o wskazówkę.
System ujawnia wskazówki stopniowo (do 4 poziomów), nie zdradzając pełnego
rozwiązania.

**Why this priority**: Funkcja edukacyjna wspierająca samodzielne myślenie —
ważna, ale nie blokuje podstawowego flow.

**Independent Test**: Można przetestować klikając „Pokaż wskazówkę" na stronie
zadania wielokrotnie i weryfikując, że każda kolejna wskazówka jest bardziej
szczegółowa, ale żadna nie zawiera pełnego rozwiązania.

**Acceptance Scenarios**:

1. **Given** uczeń jest na stronie zadania, **When** klika „Pokaż wskazówkę",
   **Then** widzi pierwszą (najogólniejszą) wskazówkę.
2. **Given** uczeń widzi wskazówkę N, **When** klika „Następna wskazówka",
   **Then** widzi wskazówkę N+1 (bardziej szczegółową), aż do maksimum 4.
3. **Given** uczeń widział wszystkie 4 wskazówki, **When** klika przycisk
   wskazówki ponownie, **Then** system informuje, że wszystkie wskazówki
   zostały ujawnione.
4. **Given** żadna wskazówka nie jest skonfigurowana dla zadania,
   **When** uczeń klika „Pokaż wskazówkę", **Then** system informuje, że
   wskazówki nie są dostępne dla tego zadania.

---

### Edge Cases

- Co się dzieje, gdy przesłany plik jest nieczytelny lub zbyt mały rozdzielczościowo?
- Jak system reaguje, gdy API Gemini jest niedostępne lub zwraca błąd?
- Czy uczeń może przesłać wiele plików (np. kilka stron rozwiązania)?
- Co się dzieje, gdy zadanie nie posiada pliku PDF (błąd danych)?
- Jak system zachowuje się przy braku konfiguracji skali punktowej dla danego etapu?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST wyświetlać listę wszystkich edycji FerMat (I–IX, 2017–2025)
  pogrupowanych według edycji i etapu (I lub II).
- **FR-002**: System MUST wyświetlać treść każdego zadania wczytaną z pliku PDF
  lub metadanych JSON.
- **FR-003**: Użytkownicy MUST być w stanie przesłać plik (JPG, PNG, PDF) ze
  swoim rozwiązaniem dla dowolnego zadania.
- **FR-004**: System MUST przekazać do AI: treść zadania (PDF), oficjalne
  rozwiązanie (jeśli dostępne: edycja 2024/2025 etap I) oraz skalę punktową
  z pliku YAML.
- **FR-005**: System MUST zwrócić ocenę liczbową oraz pisemne uzasadnienie
  w języku polskim, z informacją o nieoficjalnym charakterze oceny.
- **FR-006**: System MUST informować ucznia, gdy oficjalne rozwiązanie nie jest
  dostępne dla danej edycji/etapu, i przejść w tryb oceny bez rozwiązania.
- **FR-007**: System MUST ładować skalę punktową z pliku YAML per edycja/etap;
  brak konfiguracji MUST blokować przyjęcie zgłoszenia z czytelnym komunikatem.
- **FR-008**: System MUST przechowywać historię zgłoszeń użytkownika
  i wyświetlać ją na stronie zadania.
- **FR-009**: System MUST udostępniać progresywne wskazówki (do 4 poziomów)
  bez ujawniania pełnego rozwiązania.
- **FR-010**: System MUST wymagać zalogowania do przesyłania rozwiązań
  (przeglądanie zadań i wskazówek jest dostępne bez logowania).
- **FR-011**: Wszystkie odwołania do OMJ MUST zostać usunięte z kodu przed
  wdrożeniem — obejmuje: UI/SEO, logikę (nazwy funkcji, prompt AI), konfigurację
  Docker, credentials bazy danych, stałe aplikacji (`APP_NAME`, `SITE_URL`,
  klucze localStorage) oraz pliki e2e.

### Key Entities

- **Edycja (Edition)**: Numer edycji (I–IX), rok (2017–2025), lista etapów.
- **Etap (Stage)**: Etap I lub II w ramach edycji; posiada skonfigurowaną skalę punktową.
- **Zadanie (Task)**: Numer, treść, plik PDF, lista wskazówek; opcjonalnie: oficjalne rozwiązanie PDF.
- **Zgłoszenie (Submission)**: Przesłany plik, wynik punktowy, uzasadnienie AI, znacznik czasu, użytkownik.
- **Użytkownik (User)**: Konto ucznia; historia zgłoszeń.
- **Konfiguracja skali (ScoringConfig)**: Maksymalna liczba punktów, progi, opisy — per edycja/etap w pliku YAML.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uczeń może dotrzeć do treści dowolnego zadania z dowolnej edycji
  w nie więcej niż 3 kliknięciach od strony głównej.
- **SC-002**: Ocena AI jest zwracana w ciągu 2 minut od przesłania pliku
  w co najmniej 95% przypadków przy normalnym obciążeniu.
- **SC-003**: Każda ocena zawiera liczbę punktów oraz przynajmniej jedno zdanie
  uzasadnienia w języku polskim.
- **SC-004**: 100% ocen dla edycji innych niż 2024/2025 etap I zawiera
  wyraźną informację o braku oficjalnego rozwiązania.
- **SC-005**: Zmiana skali punktowej w pliku YAML jest widoczna w kolejnych
  zgłoszeniach bez ponownego wdrażania aplikacji.
- **SC-006**: Historia zgłoszeń ucznia jest dostępna na stronie każdego zadania,
  które uczeń wcześniej rozwiązywał.

---

## Assumptions

- Użytkownicy (uczniowie) korzystają z aplikacji na urządzeniach szkolnych lub
  domowych z dostępem do internetu i aparatem lub skanerem.
- Logowanie opiera się na istniejącym mechanizmie Google OAuth (wyłączonym
  domyślnie w środowisku deweloperskim przez `AUTH_DISABLED=true`).
- Pliki PDF zadań są pobierane skryptem CLI (`download_fermat.py`) ze strony
  https://sp221.edu.pl/zadania-z-poprzednich-edycji,171,pl i zapisywane do
  katalogu `tasks/`. Administrator wywołuje skrypt ręcznie przed wdrożeniem
  lub po ukazaniu się materiałów nowej edycji. Brak dedykowanego UI do uploadu.
- Aplikacja obsługuje jednego administratora lub małą grupę administratorów
  (SP 221) — brak dedykowanego panelu administracyjnego w tym zakresie.
- Schemat bazy danych nie wymaga zmian strukturalnych (kolumny `year`, `etap`,
  `task_number` działają identycznie dla FerMat). Przed wdrożeniem produkcyjnym
  stare dane OMJ są usuwane przez `docker compose down -v`; brak migracji Alembic.
- Skala punktowa jest jednolita dla obu etapów: zadania 1–5 są warte po 2 punkty
  (maksimum 10 pkt), zadania 6–10 są warte po 4 punkty (maksimum 40 pkt).
  Łącznie na etap: maksimum 50 punktów. Konfiguracja wpisana do YAML per etap
  z podziałem na grupy zadań.
- Identyfikatory etapów w URL i bazie danych to `etap1` i `etap2` (bez `etap3`
  obecnego w OMJ). Etykieta wyświetlana użytkownikowi to „Etap I" / „Etap II".
- Wskazówki są przechowywane jako statyczne teksty w plikach JSON zadań;
  nie są generowane dynamicznie przez AI.
- Aplikacja nie wysyła e-maili ani powiadomień push.

---

## Clarifications

### Session 2026-06-02

- Q: Jak PDFy z zadaniami trafiają do systemu? → A: Skrypt CLI `download_fermat.py` pobiera PDFy ze sp221.edu.pl do `tasks/`; administrator wywołuje ręcznie.
- Q: Czy schemat bazy danych wymaga migracji Alembic? → A: Brak zmian schematu strukturalnych; przed wdrożeniem `docker compose down -v` usuwa stare dane OMJ. Nowa czysta baza.
- Q: Jaki jest zakres usunięcia odwołań do OMJ z kodu? → A: Pełny — UI/SEO, logika funkcjonalna (`normalize_omj_score` → `normalize_fermat_score`), konfiguracja Docker, DB credentials, `APP_NAME`, klucze localStorage.
- Q: Jaki format identyfikatora etapu w URL i bazie danych? → A: Zachowaj `etap1`/`etap2` jako tech ID; etykieta UI to „Etap I" / „Etap II".
