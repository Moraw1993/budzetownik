---
stage: test
bolt: 007-household-foundation-ui
status: accepted
created: 2026-09-23T07:39:13Z
---

# Raport testów: członkowie, relacje i źródła dochodu

## Wynik

- **Testy aplikacji:** 94/94 przeszły: 68 Django, 24 izolowane Playwright i 2 rzeczywiste scenariusze Playwright.
- **Kontrole runtime:** 6/6 przeszły.
- **Kontrola jakości:** `scripts/quality.ps1` zakończył się powodzeniem: Ruff format/check, Prettier, ESLint, Stylelint i TypeScript.
- **Pokrycie procentowe:** nie było mierzone w tym bolcie; wynik nie jest deklaracją pełnego pokrycia kodu.

## Pliki testowe

- [x] `frontend/tests/records.spec.ts` — siedem scenariuszy członków, relacji i dochodów z kontrolowanym API: zapis Ownera, precyzja kwoty, edycja, archiwizacja, tryb odczytu Membera i Viewera, ponowna kontrola roli Administratora, paginacja oraz spóźniona odpowiedź po zmianie gospodarstwa.
- [x] `frontend/tests/live-records.spec.ts` — pełny przepływ HTTPS/API/PostgreSQL: Owner tworzy relację, członka i źródło dochodu, Viewer odczytuje dane, Owner dezaktywuje źródło; baza potwierdza dokładną wartość `9999999999999999.99`, status i zdarzenia audytu.
- [x] `frontend/tests/foundation.spec.ts` i `frontend/tests/live-foundation.spec.ts` — regresja kont, gospodarstw, zaproszeń, sesji i podstawowej responsywności.
- [x] Zestaw Django `accounts households runtime` — 68 testów reguł kont, izolacji gospodarstw, uprawnień i rekordów.

## Weryfikacja kryteriów

- ✅ **Osoba bez konta, relacja i powiązanie konta:** testy izolowane sprawdzają warianty, edycję i usunięcie powiązania; scenariusz live zapisuje relację i członka z kontem przez rzeczywiste API.
- ✅ **Role:** Owner i Administrator zapisują; Member i Viewer widzą dane bez aktywnych kontrolek zapisu; odmowa 403 odświeża rolę. Uprawnienia są również sprawdzane przez backend.
- ✅ **Dezaktywacja i historia:** testy sprawdzają potwierdzenie, stan archiwalny i brak aktywnej edycji. Scenariusz live potwierdza w bazie zdarzenia `created` i `deactivated` dla dochodu.
- ✅ **Formularz FR-08 i precyzja:** pola przypisania, częstotliwości, dat, płatnika, opisu, waluty i regularności przechodzą przez UI. Maksymalna kwota `Decimal(18,2)` zachowuje wartość i jest wyświetlana z walutą.
- ✅ **Paginacja i kontekst:** izolowane testy sprawdzają przejście na kolejną stronę, załadowanie 51 relacji i odrzucenie spóźnionej odpowiedzi starego gospodarstwa.
- ✅ **Stany ekranu:** puste listy, błędy i odmowa API są sprawdzone w izolowanych scenariuszach; komunikat planistyczny odróżnia kwotę domyślną od transakcji.
- ✅ **Rzeczywisty stos:** oba scenariusze live przeszły. Kontrola bazy po testach wykazała `e2e_users=0` i `e2e_homes=0`.

## Środowisko i kontrole runtime

Frontend działał za lokalnym HTTPS, z rzeczywistym backendem Django i PostgreSQL. Kontrola `scripts/verify_runtime.py` potwierdziła certyfikat, API i aplikację; trwałość rekordu oraz pliku po odtworzeniu kontenerów; odpowiedź 503 podczas zatrzymania bazy; odzyskanie działania i danych; idempotentną konfigurację oraz czytelny błąd brakującej konfiguracji. Po testach baza, backend i frontend były `healthy`, proxy działało, migracja zakończyła się kodem 0.

## Problemy wykryte i poprawione

- Rozszerzenie mapowania błędów API o pole `detail` spowodowało regresję komunikatu wygasłego zaproszenia. Usunięto `detail` z listy błędów pól; ponowny zestaw testów UI przeszedł.
- Pierwsza powtórka scenariusza live próbowała wpisywać członka podczas odświeżania po dodaniu relacji. Test czeka teraz na ponowne pojawienie się relacji przed wypełnieniem formularza. Ślad sieciowy potwierdził, że przed poprawką żądanie utworzenia członka nie zostało wysłane. Ponowny pełny przebieg: 2/2 przeszły.

## Ograniczenie i checkpoint

Raport potwierdza funkcje bolta 007. Przegląd wizualny szerokości paneli i formularzy wskazał osobny problem układu; jego korektę zaplanowano w [bolcie 009](../009-household-foundation-ui/bolt.md) przed odbiorem końcowym. Użytkownik zatwierdził raport; bolt 007 oraz stories 004–005 są ukończone.
