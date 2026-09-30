# Domknięcie po bolcie 012

## Zakres i baza

Użytkownik zlecił wykonanie niezbędnych operacji po audycie zamknięcia bolta 012. Branch `docs/task-post-bolt-012-operations` utworzono z `63e4791ed075a1fefc3bc2c15b89a01b639c9fa3`, ponieważ zadanie wymaga ukończonych zmian 011 i 012. Baza integracyjna: `origin/develop` = `f62b84a2a6525463d687e1bd4d8e0fa993477b2f`.

Construction jest complete; raporty, akceptacje oraz skrypt zamknięcia są zapisane w dokumentacji bolta 012. Naprawiono nieaktualny inception-log intentu 002 i status lokalnego wdrożenia. Nie zmieniono kodu aplikacji ani testów.

## Weryfikacja integracji

Historia, diff zmian brancha i końcowa różnica zostały porównane. Develop jest przodkiem wyniku 012; brak zmian przeciwnej strony wymagających dodatkowego scalenia. `merge-tree --write-tree` zakończył się kodem 0. Kontrola `scripts/quality.ps1` przeszła. Świeży build backendu i frontendu przeszedł. Backend ponownie przeszedł 83/83 testy na osobnej bazie testowej.

Regresja UI 42/42 i rzeczywiste E2E 5/5 mają dowody w [zatwierdzonym raporcie 012](../bolts/012-family-income-acceptance/test-walkthrough.md), dotyczącym tego samego kodu aplikacji. Jawne pominięcia starszych testów pozostają opisane w tym raporcie.

Lokalny develop jest używany przez `.runtime/git-workflow`, gdzie zastano niezacommitowane zmiany. Nie zmieniano tego katalogu ani lokalnego brancha develop. Integracja zdalna zachowuje historię i wymaga ponownego pobrania oraz sprawdzenia hasha celu bezpośrednio przed aktualizacją.

## Operations — lokalny build i dev

Build lokalny, bez wersji release, tagu Git ani publikacji do registry:

- Backend `myhomebudget-backend:local`: `sha256:03d87ecbb2fca81351a911ce1def241ef8e923b939e9a581f3f7b4c04861be8e`, 59075410 bajtów.
- Frontend `myhomebudget-acceptance-17d4acaa-source-frontend:latest`: `sha256:006273f1d20d11654a00c0b5e8954637a3b2d8154be26ab0cdf48c569f0fa3cf`, 82005387 bajtów.

Nowe obrazy uruchomiono w izolowanej instalacji dev `myhomebudget-acceptance-17d4acaa-source`. PostgreSQL, backend i frontend przeszły healthcheck; migracje zakończyły się kodem 0, proxy działa. Instalacja zawiera wyłącznie dane syntetyczne z odbioru 012. Prywatna instalacja nie została wdrożona ani zrestartowana.

Restart nowych obrazów potwierdził logowanie i dokładną zgodność snapshotów API oraz wszystkich dziewięciu tabel domenowych z odbiorem 012. Instalację testową następnie zatrzymano z zachowaniem wolumenów i dowodów.

## Kolejne bramki

Staging następnie zatwierdzono i zweryfikowano: [raport stagingu](../intents/002-family-income-management/units/003-family-income-acceptance/deployment/verification-d670985-staging.md). Produkcję również zatwierdzono i wdrożono po kopii prywatnych danych: [raport produkcji](../intents/002-family-income-management/units/003-family-income-acceptance/deployment/verification-d670985-prod.md). Monitoring pozostaje otwarty i wymaga osobnego checkpointu Operations. Release wymaga jawnego `$realease_app`; branche pozostają zachowane do stabilnego wydania. Kopie prywatnych danych opisuje [procedura kopii](backup-restore.md).
