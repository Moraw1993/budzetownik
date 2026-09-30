---
environment: prod
deployed: 2026-09-30T08:47:11Z
verified: 2026-09-30T08:49:42Z
status: passed
---

# Prywatna instalacja — odbiór aktualizacji d670985

Użytkownik zatwierdził konkretny plan wdrożenia odpowiedzią „ok” na checkpoint 3. Branch `chore/task-production-family-income` utworzono z e5bf525, ponieważ wymaga planu i odbioru stagingu. Nie uruchomiono release.

## Kopia i wdrożenie

Przy zatrzymanych frontend/backend/proxy i działającej bazie wykonano spójny pg_dump, sprawdzono pg_restore --list, skopiowano media, .env, Compose, Caddyfile i konfiguracje obrazów. Obliczono SHA256 plików kopii. Lokalizacja poza repozytorium: `C:/Users/Arek/MyHomeBudgetBackups/family-d670985-20260930T084711Z`. Kopia zawiera prywatne dane i sekrety, pozostaje poza Git. Nie przetestowano odtworzenia tej konkretnej prywatnej kopii; mechanizm odtworzenia przeszedł test na syntetycznym stagingu.

Wdrożono przypięte lokalne obrazy bez build i pull, z zachowaniem istniejących wolumenów oraz sekretów. Usługa migrate zakończyła się kodem 0; nie było nowych migracji. Przerwa obejmowała czas kopii i odtworzenia kontenerów, mniej niż trzy minuty według czasu początku kopii i końcowej weryfikacji; nie prowadzono ciągłego pomiaru dostępności.

## Wyniki

- Backend: sha256:a6d056105804063e070719f99e3c6dfbd16828eea096eb589c802354635b1ea7.
- Frontend: sha256:706851a34cdcd42f37e794a02d1d8bf639debf11585c4c122d71864dc8163982.
- Baza/backend/frontend healthy, proxy działa, backend/frontend RestartCount=0; Django check bez problemów.
- SHA256 serializacji wszystkich dziewięciu tabel domeny households identyczny przed i po wdrożeniu. Porównano wszystkie pola, w tym historię i audyt; treść prywatnych danych nie trafiła do logów.
- Liczba i SHA256 każdego pliku media zgadzają się z kopią. Nie zmieniono prywatnych danych.
- GET https://localhost:8443/api/health/ zwrócił 200 przy weryfikacji certyfikatu lokalnym CA. Nie zmieniono magazynu zaufania Windows.
- Edge: strona logowania 200, wymagane pola i przycisk obecne, widoki 1440×1000 i 390×844 bez poziomego przepełnienia. Nie logowano się na prywatne konto ani nie zmieniano hasła. Uwierzytelnienie i zapisy były sprawdzone na syntetycznym stagingu.
- Tymczasowy dump usunięto z kontenera bazy; kopia na hoście została zachowana. Kontenery produkcji pozostają uruchomione, staging/dev zatrzymane.

Dowody: folder kopii (domain-before.txt/domain-after.txt, checksums.json, images.txt) i ignorowane `.runtime/operations/family-d670985/` (certyfikat, zrzuty strony logowania, deploy.yaml, rollback.yaml). Kontrola jakości projektu przeszła.

## Ograniczenia i utrzymanie

Nie wykonano na prywatnych danych fikcyjnych zapisów ani pomiaru P95. Nie zadeklarowano pełnego monitoringu RED/SLO ani długoterminowej dostępności. Checkpoint 4 monitoringu pozostaje otwarty.

Rollback obrazów i warunki odtworzenia bazy opisuje [plan](production-plan.md). Zachować obrazy myhomebudget-backend/frontend:rollback-pre-family-20260930; backend rollbacku pochodzi z filesystemu wcześniejszego kontenera i przeszedł kontrolę runtime/migracji na stagingu. Nie odtwarzać bazy automatycznie przy zwykłej awarii kodu.

Codzienny start tej wersji używa Compose z `.runtime/operations/family-d670985/deploy.yaml`, `--no-build --pull never`. Samo `up --build` z podstawowym Compose może zbudować inną wersję aktualnego checkoutu; po takim działaniu należy ponownie sprawdzić wdrożone obrazy.
