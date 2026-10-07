---
id: ISS-2026-001
title: "Nierówne wyrównanie pól formularza dodawania umowy"
type: bug
status: resolved
reported_at: "2026-10-07T12:10:51Z"
resolved_at: "2026-10-07T12:39:33Z"
reporting_path: "Codex chat → Master Agent → Issue Agent"
affected_version: "frontend 0.1.0, snapshot from develop"
affected_commit: "202a8c5f19be6b27ca8965de4c1309511d9bb0d1"
environment: "Microsoft Edge via Playwright, local Next.js, mocked API"
module: "Frontend → Rodzina → Umowy → ContractPanel / ContractForm"
severity: low
reproducibility: confirmed
related_issues: []
---

# ISS-2026-001: Nierówne wyrównanie pól formularza dodawania umowy

## Summary

W górnym rzędzie formularza „Dodaj umowę” kontrolki „Osoba umowy” i „Nazwa umowy” zaczynały się około 27 px niżej niż selektor „Firma” i były nienaturalnie rozciągnięte.

## Exact description

Komórka „Firma” zawiera selektor i przycisk „+ Nowa firma”, dlatego wyznacza wyższy wiersz siatki. Sąsiednie elementy `.field` rozciągały się do wysokości całego wiersza. Etykiety były zasadniczo wyrównane; różnica dotyczyła położenia i wysokości kontrolek. Nowy test regresyjny odtwarza różnicę 27 px przy szerokości 1440 px przed poprawką.

## Where it happened

- **Product path / screen / URL / API:** Rodzina → Umowy → Dodaj umowę.
- **Reporting path:** Zgłoszenie w rozmowie Codex do Master Agenta.
- **Affected module:** Frontend, `contract-panel.tsx` → `contract-form.tsx`.
- **First observed:** Nieustalone.
- **Frequency:** Odtworzono powtarzalnie w teście Playwright przed poprawką.
- **Affected users/data/workflow:** Wada układu wizualnego; brak zgłoszonego blokowania wprowadzania danych.

## Steps to reproduce

1. Otworzyć aplikację i przejść do sekcji „Zarządzanie rodziną”.
2. Wybrać zakładkę „Umowy”.
3. Kliknąć „Dodaj umowę”.
4. Przy szerokości ekranu powyżej 1200 px porównać górne krawędzie i wysokości kontrolek „Osoba umowy”, „Firma” i „Nazwa umowy”.

## Expected behavior

Kontrolki pierwszego rzędu są wyrównane u góry i mają jednakową wysokość, a przycisk „+ Nowa firma” pozostaje pod selektorem bez nachodzenia na sąsiednie pola ani kolejny rząd. Węższy układ przy 1024 px zachowuje kolejność i nie powoduje przepełnienia.

## Actual behavior

Przed poprawką kontrolki osoby i nazwy były przesunięte w dół o 27 px względem firmy; input nazwy był dodatkowo o 2 px wyższy od selecta. Dowód: [zrzut bazowy 1440 px](evidence/contract-form-baseline-1440.png).

## Environment

- **Application version/build:** Frontend `0.1.0`, źródła brancha `fix/task-issue-2026-001-contract-form-layout`.
- **Base commit:** `202a8c5f19be6b27ca8965de4c1309511d9bb0d1`.
- **Verification environment:** Microsoft Edge via Playwright, lokalny Next.js uruchomiony z izolowanego worktree; odpowiedzi API były mockowane.
- **Viewports:** 1440, 1024 i 390 px.

## Severity and workaround

- **Severity:** Low — wada wizualna formularza, bez wykazanego wpływu na zapis danych.
- **Workaround:** Brak potrzeby po wdrożeniu poprawki.

## Evidence

| File | Type | Description | Captured at (UTC) |
|------|------|-------------|------------------|
| `evidence/contract-form-layout.png` | image | Zrzut zgłoszony przez testera, pokazujący rozjechane kontrolki. | unknown |
| `evidence/contract-form-baseline-1440.png` | image | Odtworzenie układu sprzed poprawki przy 1440 px; test mierzy różnicę położenia 27 px. | 2026-10-07 |
| `evidence/contract-form-fixed-1440.png` | image | Formularz otwarty przy 1440 px po poprawce. | 2026-10-07 |
| `evidence/contract-form-fixed-long-company-1440.png` | image | Formularz po poprawce z długą nazwą firmy. | 2026-10-07 |
| `evidence/contract-form-validation-1440.png` | image | Formularz po błędzie walidacji pola w pierwszym rzędzie. | 2026-10-07 |
| `evidence/contract-form-fixed-1024.png` | image | Układ dwóch kolumn przy 1024 px. | 2026-10-07 |
| `evidence/contract-form-fixed-390.png` | image | Formularz w układzie mobilnym przy 390 px. | 2026-10-07 |

## Triage and resolution

- **Owner:** Codex
- **Related bolt/task:** [Plan naprawy](../../tasks/ISS-2026-001-contract-form-layout/implementation-plan.md), branch `fix/task-issue-2026-001-contract-form-layout`.
- **Resolution:** CSS zawęża wyrównanie górnej krawędzi do pól siatki formularza umowy i ujednolica wysokość input/select do 46 px. Logika i globalne style pól bez zmian.
- **Resolved in version/commit:** `73be232c4a6c3b58cb02885592a3979ba6b0ac66`.
- **Verification:** `frontend/tests/family.spec.ts` 17/17; test ukierunkowany potwierdził przed poprawką 27 px różnicy i przeszedł po poprawce; responsywność 1440/1024/390 px 3/3. Prettier dla zmienionego TSX/CSS, ESLint, Stylelint i TypeScript przeszły. `scripts/quality.ps1` zatrzymał się na Prettierze dla 32 niezmienionych plików repozytorium; nie formatowano niepowiązanego zakresu. `git diff --check` przeszedł przed commitem `73be232`.
- **Closed at:** "2026-10-07T12:39:33Z"

## Reporter notes

Zgłoszenie dotyczy snapshotu gałęzi `develop`; naprawa została wykonana na branchu taska fix zgodnie ze standardem Git.
