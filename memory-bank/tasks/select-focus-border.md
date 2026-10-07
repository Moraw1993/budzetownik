# Poprawka obramowania przełącznika gospodarstwa

Użytkownik zgłosił nakładające się obrysy listy wyboru na zrzucie. Task `select-focus-border`, branch `fix/task-select-focus-border`, baza aktualnego origin/develop d670985. Poprawka istniejącej kontrolki, bez nowego widoku; nie wymaga nowej bramki projektu UI.

Kontener .household-switcher ma własne obramowanie, podczas gdy globalny focus-visible był rysowany na mniejszym select. Przeniesiono obrys fokusu na kontener przez :has(select:focus-visible); wewnętrzny select w tym stanie nie rysuje drugiego obrysu. Inne selecty zachowują globalny fokus. Nie zmieniono semantyki ani obsługi wyboru.

CSS: Prettier i Stylelint przeszły; scripts/quality.ps1 oraz build Next.js przeszły. Edge na szerokościach 1440 i 390: porównanie przed/po, obrys na kontenerze, zmiana opcji strzałką, Tab i zachowanie fokusu zwykłej listy. Dowody syntetyczne w ignorowanym .runtime/ui-select-border/.

Commit kodu 34b4a30. Frontend lokalnej instalacji odtworzono wyłącznie z obrazu myhomebudget-frontend:select-border-34b4a30, sha256:4abac9675ed1386a92d69f617d4f51bf6635cb4c83cfccb36ee806f4d6de4687. Healthcheck przeszedł; nie zmieniano backendu, bazy ani danych. Konfiguracja lokalnego startu .runtime/operations/family-d670985/deploy.yaml wskazuje poprawiony obraz; poprzednia konfiguracja w .runtime/ui-select-border/previous-deploy.yaml. Nie publikowano release.
