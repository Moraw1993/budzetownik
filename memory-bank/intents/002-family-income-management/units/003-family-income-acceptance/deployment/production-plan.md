# Plan aktualizacji prywatnej instalacji po bolcie 012

Status: przygotowany do checkpointu 3 Operations, bez wdrożenia produkcji. Branch `docs/task-production-family-income-plan` ma bazę `ec2f9e3` z brancha stagingu: plan zależy od jego odbioru i dowodów. Nie uruchamia release.

## Cel i stan zastany

Projekt Compose `myhomebudget` w katalogu repozytorium, dostęp https://localhost:8443. Backend/frontend/PostgreSQL healthy; migrate zakończył się 0, proxy działa. Wszystkie migracje, włącznie z households.0004_family_income, już są zastosowane. Kod kandydata pochodzi z d670985, przeszedł dev i staging. Brak nowych migracji względem prywatnej instalacji.

Wolumeny pozostają: myhomebudget_postgres_data, myhomebudget_media_data, myhomebudget_caddy_data i myhomebudget_caddy_config. Nie zmieniać sekretów, portów ani certyfikatów. Nie używać down -v.

## Konkretne obrazy

- Kandydat backend `myhomebudget-backend:family-d670985`: sha256:a6d056105804063e070719f99e3c6dfbd16828eea096eb589c802354635b1ea7.
- Kandydat frontend `myhomebudget-frontend:family-d670985`: sha256:706851a34cdcd42f37e794a02d1d8bf639debf11585c4c122d71864dc8163982.
- Obecny backend kontenera: sha256:05bdf0efd54eb137509a542a21719c7523ba36bd16c14b9f464e14886a096132. Oryginalny obraz i część jego warstw nie są dostępne, mimo że kontener działa. Tagowanie i commit tego obrazu nie powiodły się.
- Backend rollbacku `myhomebudget-backend:rollback-pre-family-20260930`: sha256:59a74b81c996f1204aebbbab3fef55398054677bfca569ce937adbac2a91f492. Utworzony przez export/import filesystemu działającego kontenera, bez wolumenów i bez odziedziczenia konfiguracji środowiska. Odtworzono user app, WORKDIR /app, PATH i polecenie Gunicorn. Import Django/Gunicorn, manage.py check i showmigrations na syntetycznej bazie stagingu przeszły. Nie jest to kopia prywatnej bazy ani media. Archiwum lokalne: ignorowane .runtime/operations/family-d670985/backend-rollback.tar.
- Obecny frontend: sha256:819b9a27e7dc46c272e5115f7f036dbb4979d1c2be4efd25e3ca3f12a45bdcab, przypięty jako myhomebudget-frontend:rollback-pre-family-20260930. Końcowa kontrola potwierdziła dostępność wszystkich czterech przypiętych obrazów.

## Gotowe konfiguracje

Lokalnie przygotowano deploy.yaml i rollback.yaml w .runtime/operations/family-d670985/. Oba pliki przeszły Prettier i compose config --quiet z prywatną konfiguracją, bez wyświetlania sekretów. Nakładają na compose.yaml wyłącznie obrazy migrate/backend/frontend.

Polecenie wdrożenia po kopii:

```powershell
docker compose -p myhomebudget -f compose.yaml -f .runtime/operations/family-d670985/deploy.yaml up -d --no-build --pull never --wait
```

Polecenie rollbacku kodu z zachowaniem bazy:

```powershell
docker compose -p myhomebudget -f compose.yaml -f .runtime/operations/family-d670985/rollback.yaml up -d --no-build --pull never --wait
```

## Wykonanie po akceptacji

1. Ponownie sprawdzić obrazy aktualnych kontenerów i zgodność kandydata oraz rollbacku z zatwierdzonymi hashami. Jeśli stan zmienił się od przeglądu, ponowić ocenę. Zachować lokalne obrazy, nie wykonywać prune.
2. Utworzyć nowy folder kopii poza repozytorium, np. C:/Users/Arek/MyHomeBudgetBackups/family-d670985-{timestamp}. Zapisać wersje obrazów i pliki wdrożenia. Sprawdzić wolne miejsce. Kopia i config.env zawierają prywatne dane; nie publikować ich ani logować zawartości.
3. Zatrzymać frontend/backend/proxy na czas kopii, pozostawiając bazę. Wykonać pg_dump przez plik w kontenerze i compose cp na hosta; skopiować media, .env, compose.yaml i Caddyfile zgodnie z [procedurą kopii](../../../../../operations/backup-restore.md). Sprawdzić pg_restore --list oraz sumy kontrolne. Przy błędzie wznowić dotychczasową wersję i przerwać aktualizację. Kopia nie została jeszcze wykonana: wymaga przerwy w zapisach na prywatnej instalacji.
4. Uruchomić przypięte obrazy kandydata bez build/pull. Nie zmieniać bazy, Caddy ani wolumenów. Zweryfikować migracje, health i brak restartów.
5. Sprawdzić stronę HTTPS, read-only stan domeny i zgodność danych z kopią; do testu logowania użytkownika nie pobierać ani zmieniać hasła. Odbiór zapisu został wykonany na syntetycznym stagingu; na prywatnych danych nie tworzyć fikcyjnych transakcji.
6. Przy błędzie wykonać rollback obrazów. Brak nowej migracji pozwala zachować bieżącą bazę. Odtworzenie prywatnej bazy z dumpu to odrębny krok tylko przy stwierdzonej utracie danych, po analizie; nie wykonywać automatycznie pg_restore --clean na produkcji.
7. Zapisać rzeczywisty wynik i commit dokumentacji. Następnie osobny checkpoint 4 dla monitoringu; obecne healthchecki nie są kompletnym monitoringiem RED/SLO.

Krótka niedostępność nastąpi podczas kopii i odtworzenia kontenerów. Czas zależy od rozmiaru prywatnej bazy i media; nie oszacowano go jeszcze wiarygodnie. Akceptacja wdrożenia nie jest wywołaniem `$realease_app` i nie publikuje GitHub Release.
