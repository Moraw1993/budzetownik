---
id: ISS-2026-001
title: "Nierówne wyrównanie pól formularza dodawania umowy"
type: bug
status: reported
reported_at: "2026-10-07T12:10:51Z"
reporting_path: "Codex chat → Master Agent → Issue Agent"
affected_version: "frontend 0.1.0, snapshot from develop"
affected_commit: "202a8c5f19be6b27ca8965de4c1309511d9bb0d1"
environment: unknown
module: "Frontend → Rodzina → Umowy → ContractPanel / ContractForm"
severity: unassessed
reproducibility: unknown
related_issues: []
---

# ISS-2026-001: Nierówne wyrównanie pól formularza dodawania umowy

## Summary

Pola w górnym rzędzie formularza „Dodaj umowę” nie są wyrównane pionowo. Selektor firmy znajduje się wyżej niż pola osoby umowy i nazwy umowy.

## Exact description

Na zrzucie ekranu selektor „Firma” zaczyna się wyżej niż sąsiadujące pola „Osoba umowy” i „Nazwa umowy” (różnica wynosi około 30 px). Przycisk „+ Nowa firma” jest umieszczony pod selektorem firmy i znajduje się w tym samym obszarze formularza. Nie ustalono jeszcze, co powoduje różnicę w położeniu kontrolek.

## Where it happened

- **Product path / screen / URL / API:** Rodzina → Umowy → Dodaj umowę; dokładny URL nieustalony.
- **Reporting path:** Zgłoszenie w rozmowie Codex do Master Agenta.
- **Affected module:** Frontend, `family-panel.tsx` → `contract-panel.tsx` / `contract-form.tsx`.
- **First observed:** Nieustalone.
- **Frequency:** Nieustalone.
- **Affected users/data/workflow:** Widoczna wada układu formularza; wpływ na możliwość uzupełnienia formularza nie został zgłoszony.

## Steps to reproduce

Wstępne kroki odtworzenia na podstawie zrzutu ekranu; nie zostały niezależnie potwierdzone:

1. Otworzyć aplikację i przejść do sekcji „Rodzina”.
2. Wybrać zakładkę „Umowy”.
3. Kliknąć „Dodaj umowę”.
4. Porównać pionowe położenie selektora „Firma” z polami „Osoba umowy” i „Nazwa umowy”.

Szczegóły konta, danych i przeglądarki są nieznane.

## Expected behavior

Pola w tym samym rzędzie formularza powinny być wyrównane pionowo. Dodatkowy przycisk „+ Nowa firma” nie powinien powodować, że selektor firmy znajduje się wyżej niż sąsiednie pola.

## Actual behavior

Selektor firmy jest widocznie wyżej niż sąsiednie kontrolki „Osoba umowy” i „Nazwa umowy”. Dowód: `evidence/contract-form-layout.png`.

## Environment

- **Application version/build:** Frontend `0.1.0`, snapshot gałęzi `develop`.
- **Commit/release identifier:** `202a8c5f19be6b27ca8965de4c1309511d9bb0d1` (`origin/develop` w chwili sporządzenia zgłoszenia).
- **Environment:** Nieustalone; zgłaszający wskazał aktualną wersję `develop`.
- **OS/device/browser/client:** Nieustalone.
- **Relevant configuration:** Nieustalone.

## Severity and workaround

- **Severity:** Nieoceniona; zgłoszono problem z układem wizualnym, bez informacji o blokadzie funkcjonalnej.
- **Workaround:** Nieustalony.

## Evidence

| File | Type | Description | Captured at (UTC) |
|------|------|-------------|------------------|
| `evidence/contract-form-layout.png` | image | Zrzut ekranu formularza pokazujący różne pionowe położenie selektora firmy i sąsiednich pól. | unknown |

## Triage and resolution

- **Owner:** unassigned
- **Related bolt/task:** pending
- **Resolution:** pending
- **Resolved in version/commit:** pending
- **Verification:** pending
- **Closed at:** pending

## Reporter notes

Zgłoszenie dotyczy aktualnej wersji gałęzi `develop`.
