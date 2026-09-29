---
stage: plan
bolt: 008-local-acceptance
status: approved
validated: 2026-09-23T20:31:48Z
created: 2026-09-23T20:27:40Z
---

# Plan odbioru lokalnego fundamentu

## Cel

Potwierdzić pełny scenariusz MVP 1, odtwarzalność kopii PostgreSQL i wolumenu załączników oraz P95 podstawowych operacji API. Wszystkie próby będą wykonywane na syntetycznych danych w oddzielnych instalacjach testowych, bez ingerencji w istniejące wolumeny i konta użytkownika.

## Zakres i wyniki

1. **Odbiór funkcjonalny (story 001):** automatyczny scenariusz sześciu kroków z `requirements.md`, obejmujący pierwsze konto na pustej instalacji, dwa gospodarstwa, członka bez konta, po dwa źródła dochodu członka i gospodarstwa (łącznie cztery), zaproszenie drugiego użytkownika jako Viewer, zmianę gospodarstwa i ponowne zalogowanie po odtworzeniu kontenerów. Uzupełniająca macierz API sprawdzi Ownera, Administratora, Membera i Viewera, brak sesji, odwołanie dostępu i bezpośrednie identyfikatory obcych zasobów.
2. **Kopia i odtworzenie (story 002):** instrukcja operatora oraz powtarzalna próba `pg_dump`, kopii wolumenu `media_data` i wymaganej konfiguracji. Odtworzenie nastąpi w drugiej, odrębnej instalacji testowej. Porównanie obejmie gospodarstwa, członkostwa, źródła dochodu, audyt oraz kontrolny plik w wolumenie załączników. Sprawdzimy trwałość po restarcie i odtworzeniu kontenerów oraz opiszemy odzyskiwanie konta i skutki usuwania wolumenów.
3. **Wydajność API (story 003):** powtarzalny pomiar podstawowych odczytów i zapisów gospodarstw, członków i źródeł dochodu przez lokalne HTTPS. Raport poda sprzęt, rozmiar danych, rozgrzewkę, poziom równoległości, liczbę pomiarów, P95 każdej operacji i porównanie z celem PRD `P95 < 500 ms`.
4. **Raport końcowy:** wynik każdego kryterium, rzeczywiste komendy i liczby testów, ograniczenia środowiska oraz wskazanie operacji wymagających poprawy, jeśli cel nie zostanie osiągnięty.

## Zależności

- Bolty 001–007 i 009 oraz jednostki runtime, API i interfejsu są ukończone. Istniejące testy Django, Playwright i `scripts/verify_runtime.py` są punktem wyjścia; wspólne scenariusze zostaną rozszerzone zamiast kopiowane.
- Testy wymagają działającego Docker Desktop z kontenerami Linux, Compose i lokalnej przeglądarki używanej przez Playwright. Po uruchomieniu Dockera przez użytkownika sprawdzono 2026-09-23T20:31:08Z, że kontenery bazy, backendu i frontendu są zdrowe, migracja zakończyła się kodem 0, a proxy działa. To istniejąca instalacja; odbiór zostanie wykonany na oddzielnych instalacjach testowych.
- Weryfikacja użyje osobnych nazw projektów Compose, wolumenów, sekretów i portów. Przed operacjami czyszczącymi zostanie sprawdzona tożsamość instalacji testowej. Kopie i dane uwierzytelniające nie trafią do repozytorium ani raportu.

## Podejście techniczne

1. Sprawdzić ponowne użycie istniejących testów API, przepływów Playwright i kontroli runtime. Dodać tylko brakujące scenariusze odbioru oraz narzędzia potrzebne do kopii, odtworzenia i pomiarów.
2. Utworzyć pierwszą pustą instalację testową z danymi syntetycznymi i przejść sześć kroków. Potwierdzić role i izolację także przez bezpośrednie żądania API, w tym brak skutków ubocznych po odmowie.
3. Zatrzymać zapis w instalacji źródłowej na czas spójnej kopii, wykonać dump bazy i kopię pliku kontrolnego, a następnie odtworzyć je w drugiej instalacji. Porównać rekordy i zawartość pliku; osobno sprawdzić zwykłe odtworzenie kontenerów na zachowanych wolumenach.
4. Na ustalonym syntetycznym zestawie danych wykonać rozgrzewkę i serię co najmniej 200 pomiarów dla każdej operacji przy równoległości 1 i 5. Obliczyć P95 metodą najbliższej rangi, zachowując osobno błędy i czas każdej odpowiedzi. Opisać obciążenie hosta i ograniczenia porównania.
5. Uruchomić `scripts/quality.ps1`, właściwe testy Django, UI i runtime oraz przejrzeć zmienione pliki. Jeżeli Docker pozostanie niedostępny, wyraźnie oznaczyć zależne wyniki jako niewykonane i nie zamykać bolta.

## Kryteria akceptacji

- [ ] Sześć kroków odbioru przechodzi na nowej instalacji testowej, a macierz ról i izolacji API potwierdza odmowy bez ujawnienia danych i bez zmian stanu.
- [ ] Kopia obejmuje bazę, wolumen załączników i wymaganą konfigurację; odtworzenie w drugiej instalacji zachowuje wskazane rekordy, audyt i plik kontrolny.
- [ ] Ponowne utworzenie kontenerów bez usuwania wolumenów zachowuje dane, a instrukcja jasno opisuje bezpieczną obsługę kopii i odzyskanie konta.
- [ ] Raport podaje warunki i P95 dla każdej wybranej operacji API oraz uczciwe porównanie z progiem `500 ms`; przekroczenia mają wskazane dalsze działania.
- [ ] Raport rozróżnia wykonane testy od planowanych, dokumentuje ograniczenia i nie korzysta z prywatnych danych użytkownika.

## Granica etapu

Ten dokument jest planem. Implementacja narzędzi i wykonanie testów zacznie się po zatwierdzeniu checkpointu planowania.
