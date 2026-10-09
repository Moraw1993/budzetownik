---
stage: implement
bolt: 016-periods-income-ui
created: "2026-10-09"
design: sidebar-v3
status: accepted
implementation_commit: 3c0d1b5
---

## Implementation Walkthrough: 003-periods-income-ui

### Summary

Zaimplementowano lata, miesiące, faktyczne przychody, podsumowania per waluta i prywatne załączniki w obecnym jasnym interfejsie. Sidebar zawiera jedną sekcję „Okresy i przychody”; formularz i pliki są dostępne z wybranego miesiąca lub wpisu, bez paska przełączania prototypów.

### Structure Overview

Shell odpowiada za sekcję, gospodarstwo i ochronę niezapisanych danych. Panel okresów koordynuje rok, miesiąc i wpis. Wspólna warstwa HTTP obsługuje JSON, pliki, pobieranie i CSRF; reguły finansowe i dostęp pozostają w istniejących API.

### Completed Work

- [x] frontend/app/components/household-shell.tsx — sekcja sidebaru i potwierdzana nawigacja przy szkicu.
- [x] frontend/app/components/application.tsx — zachowanie szkicu podczas zmiany widoczności okna.
- [x] frontend/app/components/periods-panel.tsx — kontekst i odświeżanie uprawnień z ochroną przed odpowiedziami poprzedniego okresu.
- [x] frontend/app/components/accounting-years.tsx — paginowana lista i tworzenie roku z 12 nieaktywnymi miesiącami.
- [x] frontend/app/components/accounting-months.tsx — stany i potwierdzenia aktywacji, zamknięcia i otwarcia.
- [x] frontend/app/components/income-list.tsx — historyczne nazwy, paginacja, sumy miesiąca i roku oraz usunięcie.
- [x] frontend/app/components/income-form.tsx — odbiorca, słownikowe źródła, faktyczna kwota, waluta, niezależna data, szkic i konflikty.
- [x] frontend/app/components/income-source-create.tsx — szybkie dodawanie istniejącymi formularzami, ochrona zapisu i klawiatura.
- [x] frontend/app/components/income-attachments.tsx — kolejka, dodawanie, prywatne pobieranie, usunięcie i sprawdzanie niepewnego wyniku.
- [x] frontend/app/components/other-source-form.tsx — wydzielony dotychczasowy formularz źródła.
- [x] frontend/app/components/company-dialog.tsx — wspólny dotychczasowy dialog firmy z zachowaniem fokusu.
- [x] frontend/app/components/other-sources-panel.tsx, contract-form.tsx, contract-panel.tsx, company-panel.tsx, ui.tsx — reużycie formularzy i przekazywanie zajętości.
- [x] frontend/app/components/periods-common.tsx — stany, błędy i wspólne potwierdzenia.
- [x] frontend/app/lib/api.ts — nagłówki, multipart, odpowiedzi binarne i błędy pól.
- [x] frontend/app/lib/periods-api.ts — typy i endpointy istniejących API oraz limity plików.
- [x] frontend/app/lib/income-response.ts — walidacja potwierdzenia zapisu przed kolejnymi operacjami.
- [x] frontend/app/globals.css, frontend/app/periods.css — aktualne tokeny, równe pola i responsywne układy.
- [x] frontend/tests/periods-api.spec.ts, period-fixtures.ts, periods-income.spec.ts, periods-recovery.spec.ts, periods-render.spec.ts — 24 nowe przypadki weryfikacji.
- [x] evidence/implementation-review.md — niezależny przegląd.
- [x] evidence/implementation-captures — 18 zrzutów widoków przy 1440/1024/390 px.

### Key Decisions

- **Kontekst:** rok prowadzi do miesięcy, miesiąc do przychodów, wpis do formularza i plików.
- **Kwoty i historia:** tekst dziesiętny, sumy z API, rozdzielone waluty i historyczne snapshoty.
- **Ponawianie:** niepewny przychód zachowuje klucz i dane próby; upload wymaga świeżej listy i świadomej decyzji.
- **Konflikty:** zachowany szkic i porównanie aktualnego zapisu; usunięcie po ponownym wyborze bieżącej wersji.
- **Dostęp:** odświeżanie roli i okresu po błędach; utrata członkostwa usuwa niedostępny kontekst.
- **Weryfikacja:** testowy frontend jest odizolowany od działającej aplikacji; dane i odpowiedzi UI są syntetyczne.

### Deviations from Plan

Style sekcji wydzielono do periods.css importowanego przez globals.css. Dodano walidator potwierdzenia income-response.ts oraz współdzielony CompanyDialog. To podział odpowiedzialności; wygląd i zakres pozostają sidebar-v3.

### Dependencies Added

Brak nowych zależności.

### Developer Notes

scripts/quality.ps1 oraz produkcyjny build frontendu przeszły. Cały zestaw Playwright: 67 passed, 8 skipped, 0 failed; wszystkie 24 nowe przypadki przechodzą. Pominięte istniejące testy live/acceptance wymagają osobnego środowiska i konfiguracji.

Nie jest to pełny odbiór z rzeczywistym backendem ani zakończenie etapu Test lub bolta 017. Szczegóły: [implementation-verification.md](evidence/implementation-verification.md). Implement oczekuje checkpointu użytkownika zgodnie z simple-construction-bolt.
