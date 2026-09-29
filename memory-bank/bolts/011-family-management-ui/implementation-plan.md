---
stage: plan
bolt: 011-family-management-ui
created: 2026-09-26T19:47:38Z
status: approved
---

# Plan implementacji: Zarządzanie rodziną

## Cel

Zebrać członków, umowy, inne źródła i źródła całego gospodarstwa w jednym dziale „Zarządzanie rodziną”. Oddzielić w interfejsie kwotę brutto umowy od opcjonalnej podpowiedzi przy innym źródle. Interfejs korzysta z API bolta 010 i nie tworzy przychodów miesięcznych.

## Zakres i wyniki

1. **Nawigacja i widok rodziny:** zastąpić osobne pozycje „Członkowie” i „Dochody” jedną pozycją. Widok pokazuje osoby wraz z ich źródłami oraz osobny obszar źródeł bez przypisanej osoby. Pokazuje stany puste, archiwalne rekordy i kontekst wybranego gospodarstwa.
2. **Firmy i umowy:** lista firm z dodawaniem, edycją i archiwizacją; formularz umowy do utworzenia i edycji; archiwizacja umowy. Firma może zostać dodana z formularza umowy bez utraty wpisanych danych. Lista odróżnia brutto i jego podstawę od przychodu miesiąca.
3. **Inne źródła i konwersja:** osobny formularz tworzenia i edycji źródła `other`, z wyborem osoby lub całego gospodarstwa i opcjonalną miesięczną podpowiedzią. Archiwizacja pozostaje dostępna. Jawna konwersja do umowy wymaga kompletnych danych, aktualnej wersji źródła i informacji, że nie powstaje przychód miesięczny.
4. **Typy, błędy i style:** typy odpowiedzi i żądań API firm, umów i źródeł; prezentacja błędów przy polach, w tym konfliktu wersji; układ szeroki, pośredni i mobilny z obsługą klawiatury.
5. **Weryfikacja:** testy UI scenariuszy trzech historii, regresja wcześniejszych ekranów, zrzuty szerokiego i mobilnego widoku, build i kontrola jakości.

## Zależności i ograniczenia

- Bolty `009-household-foundation-ui` i `010-family-income-api` oraz jednostka fundamentu UI są ukończone. Nowe zasoby używają istniejących sesji, CSRF, ról i ścieżek `/api/households/{id}/`.
- `IncomeSource` zachowuje UUID i `kind`; szczegóły `contract` pochodzą z osobnego endpointu. Dawne źródła mają `kind=other` do chwili jawnej konwersji. Brutto umowy nie staje się miesięczną podpowiedzią ani przychodem miesiąca (ADR-005).
- Listy API są paginowane po 50 rekordów. Grupowanie źródeł według osoby musi uwzględnić wszystkie strony, a zapis korzystać z `expected_version` dla konwersji.
- Owner i Administrator widzą akcje zapisu; Member i Viewer wyłącznie odczyt. Backend pozostaje źródłem prawdy dla uprawnień i powiązań.
- Bez nowych bibliotek, zmian schematu backendu i nowych tras Next.js, o ile przegląd implementacyjny nie ujawni rzeczywistej potrzeby.

## Przegląd ponownego użycia

- `frontend/app/components/household-shell.tsx` i `application.tsx` już utrzymują wybrane gospodarstwo oraz sekcję. Rozszerzyć tę nawigację i zachować reset widoku oraz anulowanie spóźnionych odczytów po zmianie gospodarstwa.
- `members-panel.tsx` zawiera zarządzanie osobami i relacjami; zachować formularze i akcje, dołożyć czytelną prezentację źródeł przypisanych do osoby zamiast odtwarzać obsługę członków od początku.
- `income-panel.tsx` zawiera odczyt, paginację i obsługę starszych źródeł. Rozdzielić formularz i prezentację `other` od umowy; wykorzystać istniejące operacje archiwizacji oraz mechanizm odświeżania.
- `ui.tsx` udostępnia `ActionForm`, `Field`, `SelectField`, `Panel`, `Button` i `Pagination`; wykorzystać ich obsługę stanu zapisu, walidacji pól i klawiatury. Formularz firmy otwierać jako osobny formularz obok formularza umowy, bez zagnieżdżania elementów `<form>`.
- `frontend/app/lib/api.ts` zawiera klienta sesji/CSRF, paginację i mapowanie błędów; rozszerzyć typy oraz listę pól walidacji zamiast tworzyć drugiego klienta HTTP. `money.ts` zachowuje formatowanie i normalizację kwot.
- `frontend/app/globals.css` ma obecne siatki, przewijane tabele i progi 1200/900/480 px. Rozszerzyć selektory zgodnie z nowym układem, bez powielania reguł.

## Podejście techniczne

1. Kompozycja działu rodziny pobiera dane dla bieżącego gospodarstwa, grupuje źródła po `member_id` oraz pokazuje oddzielnie `member_id=null`. Po zmianie gospodarstwa zeruje poprzedni widok i anuluje starsze żądania. Paginowane listy używają istniejącego `apiAllPages`, gdy prezentacja wymaga pełnego zestawu.
2. Formy `other` i `contract` mają osobne pola oraz jawne etykiety: „Kwota brutto” z podstawą umowy oraz „Opcjonalna podpowiedź miesięczna”. Dla umowy formularz warunkowo pokazuje stanowisko i własną nazwę typu. Dla jednorazowego źródła wyłącza regularność.
3. Tworzenie firmy podczas wypełniania umowy nie resetuje stanu umowy; po sukcesie odświeża słownik i wybiera nową firmę. Archiwalne firmy pozostają widoczne przy istniejących umowach, ale nie można wybrać ich dla nowej umowy.
4. Konwersja używa aktualnego `version`, wymaga osoby i firmy oraz danych umowy. Przy `409` pokazuje zrozumiały konflikt i odświeża dane, aby uniknąć nadpisania zmian; błędy `400` trafiają pod pola wskazane przez API.
5. Tabele i karty zachowują semantyczne nagłówki, statusy, kolejność fokusu i możliwość przewijania klawiaturą. Na 1440, 1024 i 390 px nie wolno powodować poziomego przewijania całej strony ani zasłaniać akcji.

## Kryteria odbioru

- [ ] Nawigacja ma jeden dział „Zarządzanie rodziną”; osoba widzi swoje umowy i inne źródła, a źródła gospodarstwa są osobno. Osoba bez źródeł ma stan pusty.
- [ ] Zmiana gospodarstwa nie pokazuje danych ani spóźnionych odpowiedzi poprzedniego gospodarstwa.
- [ ] Owner i Administrator mogą dodać, edytować i archiwizować firmy, umowy i inne źródła; Member i Viewer widzą dane bez akcji zapisu.
- [ ] Dodanie firmy w trakcie wpisywania umowy zachowuje pola umowy; typ umowy steruje polem stanowiska lub własnej nazwy typu. Kwota brutto i podstawa są jednoznaczne.
- [ ] Inne źródło można przypisać osobie albo gospodarstwu; podpowiedź miesięczna jest opcjonalna i nie jest prezentowana jako zrealizowany przychód.
- [ ] Jawna konwersja zachowuje identyfikator źródła, wymaga wersji, ostrzega o braku przychodu miesięcznego i obsługuje konflikt bez cichej utraty zmian.
- [ ] Archiwalne pozycje pozostają czytelne i nie mają akcji edycji. Błędy walidacji API są przy odpowiednich polach.
- [ ] Widok działa na szerokim, pośrednim i mobilnym ekranie; podstawowe przepływy można wykonać klawiaturą.
- [ ] Testy UI i regresyjne, `scripts/quality.ps1` oraz build frontendu przechodzą.
