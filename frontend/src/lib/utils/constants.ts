// Constants for FerMat Validator

export const APP_NAME = "FerMat Validator";
export const APP_TITLE = "FerMat Validator – Konkurs Matematyczny FerMat";
export const APP_DESCRIPTION =
  "Przygotuj się do Konkursu Matematycznego FerMat z pomocą AI. Archiwum zadań z wielu edycji, ocena rozwiązań przez sztuczną inteligencję, wskazówki i ścieżka nauki.";
export const CONTACT_EMAIL = "pgmichalak@gmail.com";
export const SITE_URL = "https://fermat-validator.pl";

export const CATEGORY_NAMES: Record<string, string> = {
  algebra: "Algebra",
  geometria: "Geometria",
  teoria_liczb: "Teoria liczb",
  kombinatoryka: "Kombinatoryka",
  logika: "Logika",
  arytmetyka: "Arytmetyka",
};

export const CATEGORY_TOOLTIPS: Record<string, string> = {
  algebra: "Układy równań, tożsamości algebraiczne, nierówności",
  geometria: "Geometria płaska: trójkąty, czworokąty, okręgi",
  teoria_liczb: "Podzielność, liczby pierwsze, cyfry, równania diofantyczne",
  kombinatoryka: "Zliczanie, dowody istnienia, zasada szufladkowa",
  logika: "Ważenie, optymalizacja, teoria gier, strategia",
  arytmetyka: "Średnie, stosunki, proste obliczenia",
};

export const DIFFICULTY_LABELS: Record<number, string> = {
  1: "Bardzo łatwe - podstawowe zastosowanie wzorów",
  2: "Łatwe - wymaga prostego wglądu",
  3: "Średnie - kilka kroków rozumowania",
  4: "Trudne - wymaga znacznego wglądu",
  5: "Bardzo trudne - kreatywne podejście",
};

export const HINT_LABELS = ["Zrozumienie", "Strategia", "Kierunek", "Wskazówka"];
export const HINT_ICONS = ["💡", "🎯", "🧭", "🔑"];

export const MAX_UPLOAD_FILES = 10;
export const MAX_FILE_SIZE_MB = 10;
export const ALLOWED_FILE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/heic",
];

export const ETAP_NAMES: Record<string, string> = {
  etap1: "Etap I",
  etap2: "Etap II",
  etap3: "Etap III",
};

// Mastery threshold - matches backend progress.py:get_mastery_threshold()
// FerMat tasks are worth 2 or 4 points (per-task max_score comes from the API).
// Mastery = full marks for 2-point tasks, max - 1 for larger scales.
export function getMasteryThreshold(maxScore: number): number {
  return maxScore <= 2 ? maxScore : maxScore - 1;
}

// Curated list of tasks for Etap 2 preparation
// Format: {year}_etap2_{task_num}
// TODO: Populate with actual FerMat etap2 tasks once data is available.
export const ETAP2_PREP_TASKS: string[] = [];

// Mock Etap 2 practice sets - realistic exam simulations
// Each set contains 5 tasks with typical etap2 difficulty distribution
// TODO: Populate with actual FerMat etap2 tasks once data is available.
export interface MockEtap2Set {
  id: string;
  name: string;
  tasks: string[];
}

export const MOCK_ETAP2_SETS: MockEtap2Set[] = [];

// Timer duration for etap2 (3 hours in milliseconds)
export const ETAP2_TIMER_DURATION_MS = 3 * 60 * 60 * 1000;
