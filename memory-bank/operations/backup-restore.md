# Kopia i odtworzenie lokalnej instalacji

Ta procedura obejmuje bazę PostgreSQL, wolumen `media_data` i plik `.env`. Wolumeny są trwałe po zwykłym restarcie kontenerów, ale nie zastępują kopii przechowywanej poza komputerem. Zawartość `.env` i kopii bazy może zawierać sekrety oraz dane prywatne; przechowuj ją w zabezpieczonym miejscu poza repozytorium.

## Kopia

1. Wybierz nowy folder kopii poza repozytorium. Zapisz obok niego datę, wersję aplikacji i wersję PostgreSQL. Upewnij się, że jest dość miejsca na bazę i załączniki.
2. Zatrzymaj zapisy aplikacji (`docker compose stop frontend backend proxy`), pozostawiając bazę uruchomioną. Nie używaj `docker compose down -v`: opcja `-v` usuwa wolumeny wraz z danymi.
3. Wykonaj spójny dump: `docker compose exec -T db pg_dump -U myhomebudget -d myhomebudget -Fc -f /tmp/myhomebudget.dump`. Przenieś go na hosta poleceniem `docker compose cp db:/tmp/myhomebudget.dump <folder-kopii>/database.dump`. Zapis binarnego dumpu przez operator przekierowania `>` w Windows PowerShell 5.1 może go uszkodzić, dlatego używaj `docker compose cp`.
4. Skopiuj wolumen załączników z kontenera backendu: `docker compose cp backend:/app/media <folder-kopii>/media`. Skopiuj `.env` jako `<folder-kopii>/config.env`; nie zapisuj zawartości tego pliku w logach ani w repozytorium. Zapisz także używaną wersję `compose.yaml`, `infra/Caddyfile` i obrazu aplikacji lub numer wydania, aby odtworzyć zgodną wersję.
5. Sprawdź, że plik dumpu i folder `media` istnieją, oraz oblicz sumy kontrolne. Usuń tymczasowy dump z kontenera bazy: `docker compose exec -T db rm -f /tmp/myhomebudget.dump`. Wznów aplikację poleceniem `docker compose up -d backend frontend proxy` i potwierdź stan usług.

Polecenia z `<folder-kopii>` należy wykonać po podstawieniu rzeczywistej ścieżki. W PowerShell ścieżki ze spacjami ujmij w cudzysłów. Nie uruchamiaj dwóch operacji kopii równolegle do tego samego folderu.

## Odtworzenie

1. Przygotuj oddzielną instalację tej samej wersji aplikacji i PostgreSQL. Nie podłączaj testowego odtworzenia do wolumenów bieżącej instalacji. Umieść `config.env` jako `.env` w instalacji docelowej i zabezpiecz go przed innymi użytkownikami systemu.
2. Uruchom usługi zgodnie z `README.md`, aby powstały docelowe wolumeny. Następnie zatrzymaj zapisy (`docker compose stop frontend backend proxy`).
3. Skopiuj dump do kontenera: `docker compose cp <folder-kopii>/database.dump db:/tmp/myhomebudget.dump`. Odtwórz go w docelowej bazie: `docker compose exec -T db pg_restore --exit-on-error --clean --if-exists --no-owner --no-privileges -U myhomebudget -d myhomebudget /tmp/myhomebudget.dump`. Opcje `--clean` usuwają istniejące obiekty **docelowej** bazy; sprawdź nazwę projektu Compose i instalacji przed wykonaniem.
4. Skopiuj folder załączników do docelowego kontenera: `docker compose cp <folder-kopii>/media/. backend:/app/media/`. Usuń tymczasowy dump z kontenera bazy i uruchom `docker compose up -d backend frontend proxy`.
5. Sprawdź `docker compose ps -a`, endpoint `/api/health/`, logowanie, gospodarstwa, członkostwa, źródła dochodu, audyt oraz plik kontrolny załącznika. Porównaj liczby rekordów i sumy kontrolne z kopią. Przywrócenie sesji wymaga tego samego `DJANGO_SECRET_KEY` z kopii konfiguracji.

## Odzyskanie dostępu do konta

Jeżeli po odtworzeniu hasło użytkownika jest nieznane, operator może wykonać `docker compose exec backend python manage.py recover_account LOGIN`. Polecenie pyta o nowe hasło bez wyświetlania go i unieważnia poprzednie sesje. Nie zmienia ról użytkownika.

## Próba odbiorowa

Skrypty `scripts/acceptance_stack.py` i `scripts/acceptance_flow.py` wykonują powtarzalne odtworzenie na dwóch projektach Compose z osobnymi wolumenami i portami. Dane syntetyczne oraz kopie testowe trafiają wyłącznie do ignorowanego folderu `.runtime/acceptance/`. Kolejność z folderu projektu:

```powershell
python scripts/acceptance_stack.py init
# Wstaw identyfikator wypisany przez poprzednie polecenie.
$runId = '<id-odbioru>'
python scripts/acceptance_stack.py up $runId
python scripts/acceptance_flow.py run $runId
python scripts/acceptance_stack.py backup $runId
python scripts/acceptance_stack.py recreate $runId
python scripts/acceptance_flow.py verify $runId
python scripts/acceptance_stack.py restore $runId
python scripts/acceptance_flow.py verify $runId --role target
$env:ACCEPTANCE_RUN_ID = $runId
Set-Location frontend
node node_modules/@playwright/test/cli.js test tests/acceptance.spec.ts
Set-Location ..
python scripts/acceptance_perf.py $runId
```

Pomiar działa na instalacji źródłowej po porównaniu kopii, bo dodaje własne rekordy syntetyczne. `python scripts/acceptance_stack.py stop <id-odbioru>` zatrzymuje źródło bez kasowania wolumenów; `--role target` zatrzymuje instalację odtworzoną. Wynik próby i ograniczenia środowiska należy zapisać w raporcie bolta 008. Nie przypisuj wyniku `PASS` krokom, których nie wykonano.
