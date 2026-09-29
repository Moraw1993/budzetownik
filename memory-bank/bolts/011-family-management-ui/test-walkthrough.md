---
stage: test
bolt: 011-family-management-ui
created: 2026-09-29T20:51:49Z
status: awaiting-validation
---

# Raport testów: Zarządzanie rodziną

## Wynik

- **UI: 42/42 uruchomione testy przeszły**, w tym 16 nowych scenariuszy rodziny, 8 scenariuszy członków i źródeł oraz 18 testów fundamentu aplikacji. Pełny przebieg trwał 26,5 s.
- **3 testy pominięto świadomie:** `acceptance.spec.ts`, `live-foundation.spec.ts` i `live-records.spec.ts` wymagają osobnej instalacji odbiorowej oraz jawnych parametrów uruchomienia. Nie traktujemy ich jako zaliczonych.
- Po rozszerzeniu trzech testów responsywnych o formularze i modal firmy ponowny przebieg całego `family.spec.ts` przeszedł **16/16** w 12,3 s.
- **Backend: 83/83 testy Django przeszły** w 6,436 s na odrębnym PostgreSQL 17. Obejmują reguły ról, izolację gospodarstw, migrację źródeł, integralność audytu oraz wersjonowanie i współbieżność zapisów.
- **Build i kontrola jakości przeszły:** produkcyjny Next.js; `scripts/quality.ps1` obejmujący Ruff format/check, Prettier, ESLint, Stylelint i TypeScript.
- **Pokrycie procentowe:** nie mierzono w tym etapie. Wyniki opisują wykonane scenariusze, nie procent pokrycia kodu.

## Środowisko i granice weryfikacji

UI działało w Microsoft Edge przez Playwright, z lokalnym produkcyjnym frontendem na `http://127.0.0.1:3002` i kontrolowanymi odpowiedziami API. Syntetyczne dane oraz rejestr żądań pozwalały sprawdzić pola, CSRF, role widoczne w UI, konflikty `400`/`403`/`409`, tożsamość źródeł i brak żądań tworzących przychód miesiąca. Autoryzację i rzeczywiste transakcje backendu sprawdził osobny zestaw Django; mock UI nie stanowi dowodu egzekwowania reguł przez serwer.

Testy Django korzystały z kontenera `bolt011-db-20260929`, sieci `bolt011-tests-20260929`, bazy syntetycznej i danych PostgreSQL w pamięci. Bieżący kod backendu montowano tylko do odczytu. Po testach usunięto kontener i sieć. Nie wykonywano migracji ani zapisów na instalacji użytkownika.

Pełny scenariusz przeglądarka → rzeczywiste API → baza, trwałość po restarcie i odbiór migracji na lokalnej instalacji należą do bolta 012. Pominięte starsze testy live nadal wymagają dostosowania do aktualnego UI przed użyciem w takim odbiorze; nie należy uruchamiać ich na prywatnej bazie.

## Pliki testów

- [x] [family.spec.ts](../../../frontend/tests/family.spec.ts) — zakładki i liczniki, źródła osoby/gospodarstwa, firmy i umowy, role, walidacja, modal, typy umów, konwersja, wersjonowanie, archiwum i responsywność.
- [x] [records.spec.ts](../../../frontend/tests/records.spec.ts) — tworzenie relacji, członków i źródeł, precyzja kwot, edycja i archiwizacja, role i odmowa zapisu, paginacja, spóźnione odpowiedzi oraz ustawienia dostępne klawiaturą.
- [x] [foundation.spec.ts](../../../frontend/tests/foundation.spec.ts) — regresja kont, sesji, gospodarstw, ról i zaproszeń; oczekiwania dostosowane do obecnego nagłówka i wyboru gospodarstwa.
- [x] [record-fixtures.ts](../../../frontend/tests/record-fixtures.ts) — współdzielone syntetyczne dane i obsługa API testów rodziny oraz członków; brak kopiowania drugiej implementacji fixture.

## Kryteria odbioru

| Kryterium planu | Wynik i dowód |
| --- | --- |
| Jeden dział rodziny, karty osób, źródła gospodarstwa, stany puste | ✅ Zakładki, osobne listy źródeł, rzeczywiste liczniki i osoba bez źródeł w teście rodziny; pusty widok członków w regresji. |
| Brak danych poprzedniego gospodarstwa i spóźnionych odpowiedzi | ✅ Opóźniona lista domu A nie wraca po wyborze B; regresja ustawień i opóźnionego zapisu nowego domu. |
| Owner/Administrator zapisują, Member/Viewer odczytują | ✅ Tworzenie firmy i umowy dla obu ról edycji, brak kontrolek zapisu dla obu ról odczytu; odmowa API odświeża rolę. Backend potwierdza autoryzację. |
| Firma bez utraty formularza, warunkowe pola, jednoznaczne brutto | ✅ Zapis firmy w modalu wybiera firmę i zachowuje nazwę oraz kwotę; cztery typy sterują stanowiskiem/nazwą własną; lista pokazuje brutto i podstawę. |
| Inne źródło osoby/gospodarstwa z opcjonalną podpowiedzią | ✅ Zapis obu przypisań, pustej kwoty i źródła jednorazowego; duża kwota dziesiętna zachowuje precyzję. |
| Jawna konwersja, zachowanie ID, wersja i konflikt | ✅ Ostrzeżenie przed zapisem, `expected_version`, zachowanie ID w kontrolowanej odpowiedzi, pojedynczy endpoint konwersji; konflikty edycji źródła, umowy i konwersji zamykają formularz i odświeżają dane. Rzeczywistą integralność sprawdzają testy Django. |
| Archiwum bez edycji, walidacja przy polu | ✅ Archiwizacja członka, źródła, umowy i firmy zachowuje rekord oraz usuwa akcje edycji. Błąd kwoty ma `aria-invalid` i opis dostępny dla czytnika; dane formularza pozostają. |
| Responsywność i klawiatura | ✅ 1440, 1024 i 390 px: brak przewijania całej strony w poziomie; tabele przewijane klawiaturą lokalnie; formularze i modal mieszczą się; strzałki/Home/End wybierają zakładki; Escape i powrót fokusu z modalu. |
| Testy regresji, jakość i build | ✅ 42 UI, 83 Django, build i końcowy `scripts/quality.ps1` przeszły. Trzy scenariusze live jawnie pominięte. |

## Kontrola wizualna jasnego designu

Zapisano 12 zrzutów list i formularza źródła przy trzech szerokościach do `.runtime/bolt011-tests/`. Są to lokalne artefakty odtwarzalne przez testy, poza Git. Obejrzano karty przy 1440/1024/390 px, szerokie źródła, umowy przy 1024 i 390 px oraz mobilne źródła i formularz. Jasne tło, białe powierzchnie, zielone akcje i granatowa nawigacja pozostają spójne. Na telefonie karty układają się w jedną kolumnę; tabele mają lokalne przewijanie.

- [Desktop — członkowie](../../../.runtime/bolt011-tests/Członkowie-1440.png)
- [Telefon — członkowie](../../../.runtime/bolt011-tests/Członkowie-390.png)
- [Telefon — umowy](../../../.runtime/bolt011-tests/Umowy-390.png)
- [Telefon — formularz źródła](../../../.runtime/bolt011-tests/form-source-390.png)

Nie jest to pełny audyt WCAG ani nowa punktowa ocena projektu. Wcześniejsze oceny v3 pozostają opisane w [design-qa.md](../../../design-qa.md).

## Problemy znalezione i rozwiązane

- Stare testy oczekiwały osobnych przycisków „Członkowie” i „Dochody”, tabeli członków, stale otwartych formularzy oraz tytułu z nazwą domu. Dostosowano je do zakładek, kart, formularzy na żądanie i wyboru gospodarstwa. Zachowano scenariusze domenowe oraz izolację.
- Fixture fundamentu nie obsługiwał nowych list API i kodu konfliktu ostatniego Ownera. Uzupełniono odpowiedzi zgodnie z aktualnym kontraktem.
- Poprawiono selektory nowych testów: formularze i alerty wyszukiwane w panelu zakładki nie kolidują z formularzem wylogowania i announcerem Next.js. Są to poprawki testów, bez zmian kodu aplikacji.
- Zrzut ustawień z regresji zapisywał się do historycznych dowodów bolta 009. Przeniesiono wynik do `.runtime`; przywrócono historyczny plik do stanu sprzed testów.
- Jeden wczesny przebieg zatrzymał się na sprawdzaniu dostępu; późniejsze pełne uruchomienie przeszło bez zwiększania timeoutów i bez dodawania retries. Nie ustalono przyczyny pojedynczego zdarzenia.

Nie stwierdzono otwartego błędu aplikacji w sprawdzonych scenariuszach. Cztery zastane zmiany wizualne pozostają poza commitami testów: `design-qa.md`, `household-shell.tsx`, `globals.css` oraz `design-system.md`. Wyniki dotyczą aktualnego checkoutu z tymi zmianami, nie samego czystego HEAD.

## Checkpoint

Testy i raport są gotowe do zatwierdzenia. Bolt pozostaje `in-progress`, etap `test`, do zatwierdzenia wyników przez użytkownika. Po akceptacji należy uruchomić obowiązkowy `bolt-complete.cjs`, sprawdzić statusy stories/jednostki i zapisać formalne zamknięcie w commicie.
