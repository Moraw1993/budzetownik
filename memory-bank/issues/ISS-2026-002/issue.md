---
id: ISS-2026-002
title: "Dodawanie źródła przesuwa formularz przychodu"
type: bug
status: in-progress
reported_at: "2026-10-09T20:30:18Z"
reporting_path: "User report in implementation chat"
affected_version: "local develop build"
affected_commit: "63df3c6176d1a32c9fb601e347a6ae280b948551"
environment: local
module: periods-income-ui
severity: low
reproducibility: always
related_issues: []
---

# ISS-2026-002: Dodawanie źródła przesuwa formularz przychodu

## Summary

Użytkownik zgłasza zbędny blok „Brakuje źródła?” i rozwijanie dużego formularza pod przychodem. Prosi o opcję w liście źródeł otwierającą krótki modal na przyciemnionym tle.

## Exact description

Raport użytkownika: formularze źródeł wyglądają inaczej w przychodach i zarządzaniu gospodarstwem. Inspekcja kodu: oba korzystają z ContractForm i OtherSourceForm oraz tego samego API; różni się kontener i wybór rodzaju. IncomeSourceCreate jest panelem w zwykłym przepływie dokumentu.

## Where it happened

- Product path: https://localhost:8443/ → Okresy i przychody → aktywny miesiąc → Dodaj przychód.
- Reporting path: wiadomość użytkownika.
- First observed: unknown; reported during current local build.
- Frequency: stałe zachowanie kodu; dostarczonego zrzutu brak.
- Impact: przesunięcie strony i nadmiar miejsca, bez utraty danych.

## Steps to reproduce

1. Owner/Administrator otwiera formularz przychodu w aktywnym miesiącu.
2. Wybiera osobę albo gospodarstwo.
3. Uruchamia „+ Dodaj źródło do słownika”.

## Expected behavior

Opcja „+ Dodaj nowe źródło…” w słowniku otwiera modal; strona nie zmienia układu. Formularz przychodu zachowuje kwotę, walutę, datę i pliki. Nadal nie wolno wpisywać dowolnego źródła poza słownikiem.

## Actual behavior

Osobne CTA i panel pod formularzem. Rodzaje źródeł i modele nie są zdublowane.

## Environment

- Windows, lokalny Docker Compose, browser version unknown.
- Commit: 63df3c6; brak nowego wydania.
- Umowa bez daty końcowej: już dozwolona przez frontend, serializer i model. Prośba o jasne oznaczenie jest poprawą czytelności, nie potwierdzonym błędem walidacji.

## Severity and workaround

- Low: zbędna przestrzeń i niespójna prezentacja.
- Workaround: źródło można dodać wcześniej w zarządzaniu gospodarstwem.

## Evidence

| File | Type | Description | Captured at (UTC) |
| --- | --- | --- | --- |
| evidence/README.md | other | Ścieżki i wynik inspekcji kodu | 2026-10-09T20:30:18Z |

## Triage and resolution

- Owner: implementation agent.
- Related task: income-source-dialog; related bolt: 016-periods-income-ui (already complete).
- Resolution: opcja w słowniku i kompaktowy modal ze wspólnymi formularzami; wyraźnie opcjonalny koniec umowy.
- Resolved in version/commit: 4b132b8 (task-income-source-dialog, develop integration tracked in PR).
- Verification: 72PASS Playwright, scripts/quality.ps1 PASS, Docker build PASS, final independent review accepted8.6/8.4 and11/11PASS. Evidence in ../../tasks/income-source-dialog/evidence/ui-design/.
- Closed at: 2026-10-09T20:52:08Z.

## Reporter notes

Umowa może mieć czas nieokreślony. Zachować to zachowanie i pokazać użytkownikowi znaczenie pustej daty końcowej.

## Ponowne zgłoszenie — 2026-10-09T21:14:03Z

Użytkownik dostarczył trzy obrazy:1/2przy60% powiększenia i3z rzeczywistym formularzem rodziny przy100%. Potwierdzają, że tworzenie w rodzinie pozostało dużym panelem inline, a modal przychodu ma inny układ. Poprzednie zamknięcie ISS dotyczyło tylko CTA i modala przychodów; nie dowodziło identyczności obu wejść. Issue ponownie in-progress, task unified-source-dialog.

Obrazy użytkownika nie są kopiowane do repozytorium (zawierają dane konta). Oryginały w załącznikach tej rozmowy. Nowe makiety i testy wykorzystują wyłącznie dane syntetyczne. Weryfikacja obu wejść przy100% obejmuje1920x950,1440x800,1366x650 oraz390x740, szczegóły rozwinięte, bez zmniejszania typografii i bez CSSzoom.