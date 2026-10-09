---
stage: plan
bolt: 016-periods-income-ui
created: "2026-10-09T05:36:59Z"
version: sidebar-v3
status: accepted
base: 29fc7e3744e11c3a8c48932e816ca2d4e01a59b8
---

# Plan implementacji — okresy i przychody

## Cel i checkpoint

Użytkownik wybiera rok i miesiąc, świadomie zarządza stanem okresu, zapisuje faktycznie otrzymane przychody oraz przegląda sumy i prywatne potwierdzenia. Zakres obejmuje pięć stories bolta 016; 013–015 i 011 są zakończone na bazie develop 29fc7e3.

Wersja sidebar-v3 zachowuje obecny HouseholdShell: granatowy sidebar 248 px, topbar, nazwę Domowe Finanse, selektor gospodarstwa i jasną treść. Jedyna nowa pozycja nawigacyjna to „Okresy i przychody”. Kanwy PNG z 8 października są wyłącznie inspiracją — użytkownik potwierdził 9 października pozostawienie sidebaru. Ich górna nawigacja nie jest częścią projektu.

Plan sidebar-v3 zaakceptowano komendą „rozpocznij implementacje”; aktualny etap to Implement. Przed kodem produkcyjnym wymagane są ocena rzeczywistych wizualizacji przez osobnego subagenta (każdy widok >7,5/10 bez blokad) oraz jawna akceptacja tej wersji przez użytkownika. Kontynuacja nie jest traktowana jako akceptacja jeszcze nieocenionego projektu. Odizolowane HTML/CSS w evidence są wizualizacją, nie integracją do aplikacji.

## Zakres i mapa widoków

| Widok                | Story   | Wizualizacja v3  | Interakcje                                             |
| -------------------- | ------- | ---------------- | ------------------------------------------------------ |
| Lata                 | 001     | years.html       | Lista, wybór roku, panel nowego roku, paginacja        |
| Miesiące             | 001/002 | months.html      | 12 miesięcy, wybór okresu, potwierdzenia stanu         |
| Przychód             | 003/004 | income.html      | Dodanie/edycja, odbiorca, słownikowe źródło, quick-add |
| Lista i podsumowanie | 004/005 | summary.html     | Wpisy, paginacja, sumy, edycja/usunięcie, załączniki   |
| Załączniki           | 005     | attachments.html | Kolejka, upload, prywatny download, usunięcie          |

Pliki powyżej znajdują się w evidence/ui-design/sidebar-v3/. Każdy zawiera główny ekran oraz pokazane poniżej warianty normalny, pusty, ładowania, błędu i sukcesu; subwidoki/formularze pomocnicze są oznaczone identyfikatorami Y-add, M-confirm, I-source, S-delete, A-delete, I-unknown, I-conflict/I-merge. Na mobile obowiązuje ten sam responsywny HTML i układ jednej kolumny; szeroka tabela ma własny obszar przewijania.

## Źródła prawdy i dostęp

- Owner/Administrator: tworzenie roku, przejścia miesięcy; zapis/edycja/usunięcie przychodu i upload/usunięcie pliku tylko w aktywnym miesiącu.
- Member/Viewer: odczyt lat, miesięcy, wpisów, sum i pobieranie uprawnionych załączników we wszystkich stanach. Brak CTA sugerujących możliwość zapisu.
- Stan z API, brak optymistycznej zmiany stanu miesiąca. Odpowiedź sukcesu i ponowny odczyt potwierdzają wynik.
- 401/403: komunikat o dostępie, odświeżenie sesji/członkostwa, usunięcie niedozwolonych akcji. 404: niedostępne dane i powrót do listy, bez ujawniania danych obcego gospodarstwa.
- Zmiana gospodarstwa czyści okres, wpis, kolejkę plików i lokalny formularz dopiero po potwierdzeniu utraty niezapisanych danych. Przestarzała odpowiedź z poprzedniego kontekstu jest ignorowana; podobnie przy zmianie osoby lub miesiąca. Stan widoku ma klucz household/year/month/income.
- Historia korzysta z recipient_snapshot i source_snapshot wpisu, również gdy osoba/źródło zostały zarchiwizowane. W edycji dotychczasowa wartość jest opisana jako historyczna; nie wysyłamy niezmienionego powiązania ponownie, jeśli backend dopuszcza aktualizację innych pól.

## Lata — Y i Y-add

Nagłówek i przycisk „Dodaj rok” tylko dla edytora. Karty lat mają nazwę, „12 miesięcy” oraz „Zobacz miesiące”. Widok nie prezentuje nieistniejącego stanu roku.

Endpoint listy lat nie zawiera stanów miesięcy ani sum. W tym ekranie nie wyświetlamy takich agregatów i nie wykonujemy 12 zapytań na kartę. Sumy roku są w podsumowaniu wybranego okresu. Paginacja respektuje count/next/previous. Linki next są walidowane jako ścieżki tej samej API i kontekstu, nie wykonywane bezwarunkowo.

„Dodaj rok” otwiera inline panel Y-add. Pole Rok, liczba całkowita 1–9999, domyślnie bieżący rok lokalny, komunikat „Powstanie 12 nieaktywnych miesięcy”. Anuluj zachowuje listę. Po 201 pokazujemy sukces i 12 nieaktywnych miesięcy nowego roku. Błąd duplikatu pokazuje „Ten rok już istnieje — wybierz go z listy”; odświeżenie listy nie aktywuje żadnego miesiąca. Timeout nie wywołuje automatycznego POST retry; najpierw odczyt listy.

Pusty stan: brak lat; CTA tylko Owner/Admin. Czytelne ładowanie i błąd z „Spróbuj ponownie”. Zapis ma busy, chroni przed podwójnym kliknięciem.

## Miesiące — M i M-confirm

12 kart w kolejności styczeń–grudzień, desktop 3–4 kolumny zależnie od dostępnej przestrzeni, mobile jedna. Każda karta: nazwa miesiąca, tekstowy stan, „Przychody”. Nawigacja do nieaktywnego lub zamkniętego miesiąca jest dozwolona i nie zmienia stanu.

Akcje zależą od stanu: Nieaktywny → Aktywuj; Aktywny → Zamknij; Zamknięty → Otwórz ponownie. Brak deaktywacji. Każda akcja ma inline potwierdzenie M-confirm z nazwą roku/miesiąca, wyjaśnieniem skutku, Anuluj i konkretnym przyciskiem („Aktywuj kwiecień”, „Zamknij kwiecień”, „Otwórz kwiecień”). Zamknięcie opisuje blokadę zmian, otwarcie pozwolenie na zmiany. To jeden wzorzec panelu potwierdzenia, nie nowy modal.

Karty nie pokazują fikcyjnego zera, jeśli endpoint nie dostarcza sum. Stan ładowania, błąd i konflikt są widoczne przy konkretnej operacji. 409 wymusza odczyt miesięcy i pokazuje aktualny stan; brak samodzielnej zmiany badge. Wiele aktywnych i dowolna kolejność są dozwolone.

## Lista przychodów i sumy — S i S-delete

Stały kontekst gospodarstwo/rok/miesiąc, tekstowy badge stanu. Dwie grupy sum: miesiąc i rok, wszystkie waluty osobno. Dane wyłącznie income-totals, bez sumowania float w UI. Puste totals to „Brak przychodów”, nie wymyślone zero waluty. Błąd jednej sumy nie jest zerem i nie ukrywa listy ani drugiej grupy.

Lista używa historycznych nazw, kwoty/waluty, daty otrzymania oraz akcji „Załączniki”. API listy nie zwraca liczby plików, więc nie projektujemy kolumny z wymyślonymi licznikami ani N+1 dla każdego wpisu. Paginacja 50 rekordów; sumy dotyczą całego okresu, nie widocznej strony.

Owner/Admin w active: „Dodaj przychód”, Edytuj, Usuń. S-delete to potwierdzenie inline z odbiorcą/kwotą i informacją o logicznym usunięciu; DELETE zawiera expected_version. Po sukcesie odświeżamy listę i obie sumy, nie usuwamy pozycji przed odpowiedzią.

Closed/inactive: komunikat tylko do odczytu. Owner/Admin może przejść do odpowiedniej potwierdzanej akcji stanu, Member/Viewer otrzymuje objaśnienie. Nieaktywna nawigacja nie tworzy wpisów.

## Formularz — I, edycja i I-source

Kolejność: typ odbiorcy (osoba/gospodarstwo), osoba jeśli wybrana, źródło słownikowe, podgląd aktywnej umowy/podpowiedzi, faktyczna kwota, waluta, data otrzymania, opcjonalna kolejka plików.

Wybór osoby pobiera paginowane income-source-options dla okresu/osoby. Gospodarstwo używa zapytania bez member_id. Zmiana odbiorcy kasuje wybrane źródło i dotychczasowy podgląd; nie kasuje kwoty/daty. Zmiana źródła nie nadpisuje ręcznie wprowadzonej kwoty. Kwota nowego wpisu jest pusta; umowa/podpowiedź pozostaje oddzielną informacją. Lista opcji musi pobrać kolejne strony, aby dostępne źródło nie znikło po 50 pozycjach.

Jedno źródło na wpis. Kilka wpływów z różnych źródeł to osobne wpisy. Brak pola dowolnej nazwy zamiast source_id.

Szybkie dodanie I-source: inline podpanel w formularzu, wybór „Inne źródło” lub „Umowa”. Reużywa istniejących formularzy OtherSourceForm i ContractForm po wydzieleniu ich z paneli. Każdy zawiera obecne obowiązkowe pola, a umowa istniejący słownik firm i zatwierdzony dialog nowej firmy. Nowe źródło nie tworzy przychodu. Zapis → ponowny odczyt opcji → wybór utworzonego id tylko jeśli kwalifikuje się dla odbiorcy/okresu; w przeciwnym razie jawne „Źródło zapisane, ale nie jest dostępne w tym okresie” i możliwość poprawy. Dane przychodu i pliki pozostają w pamięci. Anuluj wraca do formularza, nie zapisuje źródła.

Kwota dodatnia 0,01–9999999999999999,99, maksymalnie 2 cyfry dziesiętne. normalizeDecimal/formatMoney z istniejącego money.ts; nie parsujemy kwot przez Number. Waluta trzy wielkie litery zgodnie z API (bez nowego słownika kursów). Data otrzymania wymagana, może być poza miesiącem/rokiem; nigdy nie zmieniamy przez nią okresu.

POST przychodu z UUID Idempotency-Key dla logicznej próby. Przy nieznanej odpowiedzi zachowujemy ten sam klucz i dokładny payload do ręcznego retry. Zmiana payloadu po nieznanym wyniku wymaga najpierw sprawdzenia poprzedniej próby; nie generujemy nowego klucza tylko z powodu retry. Przy potwierdzonym błędzie walidacji i zmianie danych nowa próba może otrzymać nowy klucz. PATCH z expected_version, tylko zmienione pola. 409 stale-version zachowuje lokalny szkic, prezentuje aktualny zapis i wymaga jawnego ponowienia po porównaniu; nie nadpisuje cudzej zmiany.

Po potwierdzonym zapisie przychodu dopiero upload plików. Wpis i pliki nie są jedną transakcją HTTP. Komunikat „Przychód zapisany, załączniki nie zostały dodane” zawiera link do konkretnego przychodu. Retry plików nigdy nie tworzy ponownie przychodu. Anuluj/nawigacja przy zmianach prosi o potwierdzenie; dane szkicu i File są w pamięci, bez localStorage finansowych danych/plików.

## Załączniki — A i A-delete

Kontekst: historyczny odbiorca/źródło, kwota, data otrzymania, okres. Lista plików z nazwą, typem, rozmiarem, Pobierz; przy active Owner/Admin także Usuń i Dodaj pliki. Pliki usunięte nie wracają do listy.

Kolejka przed uploadem odróżnia pliki oczekujące od już zapisanych. 1–5 plików na request, do 10 MiB/plik, 25 MiB/batch; 20 aktywnych i 50 MiB na wpis. Wstępne sprawdzenie rozmiaru/liczby/rozszerzenia nie zastępuje serwerowej walidacji zawartości. PNG/JPG/JPEG/PDF, binary limits opisane jako MiB. Listę/capacity odczytujemy przed zapisem i po nim.

FormData: repeated files, credentials same-origin, świeży CSRF jak w api.ts, przeglądarka ustawia multipart boundary. Nie ustawiamy ręcznie JSON Content-Type. Sukces uploadu wymaga 201 i poprawnego results z metadanymi, nie dowolnego 2xx. Batch all-or-nothing po stronie API; UI nie oznacza wybranych plików jako zapisanych przed odpowiedzią.

Timeout/utrata połączenia nie gwarantuje rollbacku. Stan „Nie znamy wyniku dodawania plików. Sprawdź listę przed ponowieniem”, przycisk „Sprawdź listę”. Brak automatycznego retry. Serwer nie ma checksum w publicznych metadata; podobna nazwa/rozmiar nie dowodzi duplikatu. Po odczycie użytkownik świadomie decyduje o kolejnym uploadzie, jeśli wynik nadal niejasny. Zapisujący się upload nie dostaje pozornego progresu procentowego; pokazujemy zajętość i liczbę wybranych plików.

Download same-origin authenticated endpoint; bez public URL/storage key. Odpowiedź 401/403/404/5xx prezentuje błąd w widoku. Dla obsługi błędów blob fetch i object URL jest tworzony tylko po poprawnej odpowiedzi; URL zwalniamy po użyciu. Zamknięty/nieaktywny miesiąc zachowuje uprawniony odczyt. A-delete: osobne inline potwierdzenie z nazwą pliku i konkretną akcją „Usuń załącznik”.

## Responsywność i dostępność

- 1440/1024 desktop: obecny sidebar/topbar, content 32 px, białe panele radius16, Geist, tokeny z globals.css.
- <=900 sidebar zgodnie z obecną aplikacją przenosi się nad treść. Nie dokładamy drugiego shellu. 390/480 jedna kolumna pól i kart, akcje zawijane, input/select jednakowe minimum44px; dodatkowe quick-add nie rozciąga sąsiedniego pola.
- Tabela ma aria-label i tabindex=0 w podpisanym regionie przewijania; nie powoduje scrolla całej strony. Na telefonie opcjonalnie prezentacja wpisów jako czytelne karty bez ukrywania kwoty/dat/akcji.
- Widoczne label, field-error aria-describedby, aria-invalid, statusy tekstowe. Fokus3px o kontraście właściwym dla powierzchni; brak informacji wyłącznie kolorem.
- Po wejściu w widok fokus na nagłówku, po otwarciu inline panelu na pierwszym polu; Anuluj przywraca fokus do triggera. Escape zamyka pomocniczy panel po uwzględnieniu niezapisanych zmian. Nowe inline panele nie wymagają focus trap; historyczny modal firmy zachowuje swój wzorzec.
- Ładowanie aria-busy i status role=status; błędy role=alert, sukces role=status. Nie usuwamy formularza i wartości po błędzie. Disabled CTA ma jawne objaśnienie. Podczas zapisu blokujemy ponowny submit.
- Komunikaty UI bez surowych stosów, ścieżek storage, timeoutów infrastruktury czy kluczy technicznych.
- Wizualizacja HTML jest statyczna i nie dowodzi działania klawiatury, fokusu czy API; to osobny obowiązek implementacji/testów.

## Pliki i reużycie

| Plik                                                                                  | Odpowiedzialność                                                                                                      |
| ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| frontend/app/components/household-shell.tsx                                           | Nowa istniejąca sekcja periods i nagłówek/kontekst                                                                    |
| frontend/app/components/application.tsx                                               | Stan wybranej sekcji bez regresji logowania i gospodarstw                                                             |
| frontend/app/lib/periods-api.ts                                                       | Typy lat/miesięcy/wpisów/sum/plików oraz endpointy; korzysta z api                                                    |
| frontend/app/lib/api.ts                                                               | Rozszerzenie błędów pól, headers dla Idempotency-Key, multipart/binary bez kopiowania CSRF                            |
| frontend/app/components/periods-panel.tsx                                             | Koordynacja kontekstu i nawigacji                                                                                     |
| frontend/app/components/accounting-years.tsx                                          | Y/Y-add                                                                                                               |
| frontend/app/components/accounting-months.tsx                                         | M/M-confirm                                                                                                           |
| frontend/app/components/income-list.tsx                                               | S/S-delete i grupy sum                                                                                                |
| frontend/app/components/income-form.tsx                                               | I, szkic i zapisy                                                                                                     |
| frontend/app/components/income-attachments.tsx                                        | A/A-delete i kolejka                                                                                                  |
| frontend/app/components/other-sources-panel.tsx oraz wydzielony other-source-form.tsx | Reużywalny obecny formularz źródła                                                                                    |
| frontend/app/components/contract-form.tsx                                             | Reużycie istniejącego formularza umowy, bez nowej domeny                                                              |
| frontend/app/components/ui.tsx                                                        | Istniejące Field/SelectField/Button/Panel/ActionForm; ewentualny wspólny inline confirmation przy realnym powtórzeniu |
| frontend/app/globals.css                                                              | Tokeny i ograniczone style sekcji; bez zduplikowanych selektorów                                                      |
| frontend/tests/periods-income.spec.ts                                                 | Przepływy UI, role, błędy i geometria                                                                                 |

Na etapie implementacji sprawdzamy rzeczywiste sygnatury przed wydzieleniem formularzy. Nie tworzymy drugiej logiki reguł kwot, źródeł, CSRF ani autoryzacji. Zależności npm pozostają obecne; brak wykresów i nowych bibliotek.

## Weryfikacja i kolejność implementacji po akceptacji

1. Warstwa typów/API + przełączenie sekcji i lat/miesięcy.
2. Lista/sumy i formularz z istniejącymi źródłami; quick-add przez wspólny formularz.
3. Załączniki i obsługa utraty odpowiedzi, konfliktów, access refresh.
4. Weryfikacja każdej spójnej części, commit przed następnym zakresem. Formatter/lint bezpośrednio po zmianie źródła.
5. Odbiór na rzeczywistym Compose /api: 1440/1024/390, brak poziomego overflow strony, geometria pól, teksty, role, klawiatura, fokus, potwierdzenia i success/error.
6. Scenariusze: 12 inactive po roku; wiele active w dowolnej kolejności; close/reopen; wpisy osoba/gospodarstwo; daty poza okresem; brak automatycznego brutto; słownikowy quick-add; suma wielu walut; read-only; historyczne nazwy; pagination >50; optimistic version conflict; idempotent ręczny retry; częściowy sukces income+files; nieznany upload; zakaz automatycznych duplikatów; pobranie i usunięcie pliku.
7. scripts/quality.ps1; Django regresja odpowiednia do wspólnej warstwy; migracje nie są planowane. P95 i pełny końcowy odbiór należą do bolta 017.

## Poza zakresem

Kalendarz dzienny wydarzeń, wydatki, konwersja walut, automatyczne generowanie przychodu z umowy, bank import, OCR, nowe profile osoby, publiczne linki do plików. Brak release i restartu działającej aplikacji w Plan.

## Dowody i status

- Wersja: sidebar-v3; wszystkie pięć ekranów i pomocnicze panele wymagają oceny.
- Raport niezależny: evidence/ui-design/sidebar-v3/review.md (powstanie po ocenie).
- Próg: wynik każdego widoku, nie średnia całej aplikacji, >7,5 i brak blokad.
- Zgoda użytkownika na konkretną ocenioną wersję: udzielona przed implementacją.

## Poprawki po niezależnym review v2

Wersja v2 miała dwa blokujące braki wizualizacji formularza. V3 zawiera I-unknown/I-checking/I-recovered: ręczne „Sprawdź i dokończ poprzedni zapis” używa POST z tym samym UUID i identycznym payloadem. To jawne ponowienie logicznej próby, nie fikcyjny GET po kluczu. Szkic tej próby jest zablokowany i upload nie rusza przed potwierdzeniem. API zwraca utrwaloną odpowiedź po tym samym kluczu nawet po zamknięciu okresu. Po replay odczytujemy aktualny wpis; jeśli w międzyczasie został usunięty lub utracono dostęp, pokazujemy niedostępność i nie wysyłamy plików ani nie tworzymy nowego wpisu.

I-conflict pokazuje dwa zestawy danych (szkic / aktualny zapis) z kwotą i datą oraz odbiorcą/źródłem. I-merge zaczyna od aktualnych danych i oczekuje ręcznego wyboru; PATCH używa nowo pobranej wersji. Kolejny konflikt ponownie porównuje, nigdy automatycznie nie nadpisuje. I-edit obejmuje odbiorcę i źródło, z zachowaniem historycznych powiązań przy zmianie innych pól. I-unsaved-changes pokazuje potwierdzenie utraty szkicu. Pasek „Podglądy ekranów” i stos wariantów należą tylko do narzędzia oceny, nie do produkcyjnej nawigacji.

V3 dodatkowo rozdziela sukces usunięcia załącznika od uploadu i pokazuje A-long/S-boundary dla długiej nazwy i kwoty granicznej na mobile. CSS pozwala zawinąć długi basename oraz wszystkie cyfry dużej kwoty bez overflow strony.

Akceptacja nie zmienia projektu sidebar-v3. Hash planu w historycznej recenzji odpowiada snapshotowi commita 7a9dfd8 sprzed aktualizacji metadanych postępu.
