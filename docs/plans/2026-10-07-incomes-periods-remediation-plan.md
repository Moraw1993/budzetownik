# Plan naprawy incomes/periods i boltów 013–017

Data: 2026-10-07. Limit dokumentu: 700 linii, łącznie z tabelami i przykładami.
Źródło: [review R01–R17](../reviews/2026-10-07-incomes-periods-bolts-013-017.md), commit `f0ea10d`.
Branch planu: `docs/task-incomes-periods-remediation-plan`, baza: `f0ea10d`.
Baza zawiera niescalony bolt 013 i raport review; dlatego użyto jej zamiast `origin/develop`, po `git fetch origin`.
Właściciel wykonania: czat „Kontynuuj specsmd master agent”, ID `01a0eedd-6b59-7de0-afba-7ba8c7c8b291`.

## 1. Cel i granica autoryzacji

Usunąć odtworzony błąd słownika i doprowadzić wszystkie R01–R17 do sprawdzalnych kontraktów, implementacji oraz dowodów odbioru.
Użytkownik zlecił przygotowanie planu i przekazanie implementacji do wskazanego czatu.
Ten dokument nie zamyka boltów i nie zastępuje wymaganych checkpointów DDD ani bramki UI.
Poniższe decyzje D1–D6 są kompletnymi propozycjami do zatwierdzenia w odpowiednim checkpointcie, nie zapisami wcześniejszej zgody użytkownika.
Agent może od razu wykonać regresję R01 i synchronizację dokumentacji potwierdzonego API.
Przed kodem zależnym od D1–D6 przedstawi konkretny zestaw decyzji odpowiedniego etapu, zamiast zadawać ogólne pytania o cały system.
Nie pytać ponownie o przekazanie pracy ani rozpoczęcie naprawy — zostały zlecone.
Każdy brak zatwierdzenia decyzji oznacza wstrzymanie zależnego fragmentu; niezależne prace kontynuować.

## 2. Stan wejściowy i organizacja wykonania

- Na bazie review 013: `in-progress`, Stage 5 `test`; 014–017: `planned`.
- Kod rzeczywistych przychodów i załączników jeszcze nie istnieje; źródła/umowy są konfiguracją, nie księgą wpływów.
- Ostatnie dowody review: 20/20 testów okresów i family-income, jakość PASS, osobne odtworzenie R01 i `reopen(active)`.
- Nie traktować tych dowodów jako testów nowych implementacji, pełnego E2E, aktualnego coverage ani P95.
- Odczytać live Git/statusy/AGENTS/standardy i diff przed rozpoczęciem; oba czaty używają tego samego katalogu.
- Zachować zastane zmiany. Nie nadpisywać brancha ani checkoutu używanego przez inne aktywne prace.
- Oddzielny fix-task dla R01; replanning i kontrakty na osobnym docs-task; implementacje na branchach właściwych boltów.
- Nowe niezależne branche z aktualnego `origin/develop`; zależności od niescalonego 013/planów odnotować z hashem bazy.
- Plan i review są w historii bieżącego brancha; przy przejściu na inny branch zachować dostęp do obu dokumentów przez jawne przeniesienie commitów dokumentacji.
- Nie scalać całego brancha planu do develop tylko po to, by przenieść dokumenty: zawiera również niescaloną historię 013.
- Każdy spójny, zweryfikowany etap kończy się lokalnym commitem; przed integracją standardowe fetch/porównanie/merge-tree i ponowna weryfikacja.
- Release wyłącznie po jawnej komendzie użytkownika `$realease_app`; ten handoff jej nie wywołuje.

## 3. Etap A — naprawa R01 w istniejącym słowniku

Pliki wejściowe: `backend/households/record_services.py`, `family_income_services.py`, testy family-income oraz formularz `other-sources-panel.tsx`.
Wyszukać istniejący mechanizm sprawdzania relacji; współdzielić go tylko tam, gdzie semantyka jest rzeczywiście taka sama.
Docelowa reguła: zachowanie istniejącego `member_id` nie wymaga ponownej aktywności osoby; nowe przypisanie wymaga aktywnej osoby własnego gospodarstwa.
Nie wyzerowywać właściciela i nie zmieniać go na gospodarstwo jako obejścia.
Nie rozszerzać automatycznie wyjątku na nowe relacje `account_id/relation_type_id` bez sprawdzenia ich kontraktów.

Testy obowiązkowe:

1. Utworzyć źródło dla osoby, zarchiwizować osobę, PATCH pełnym payloadem formularza z tym samym ID i aktualną wersją → `200`, właściciel zachowany.
2. PATCH bez `member_id` → `200`, właściciel zachowany.
3. Przypisanie nowego źródła lub zmiana właściciela na archiwalną osobę → `400`, brak zmian i audytu mutacji.
4. Przypisanie osoby obcego gospodarstwa → odmowa bez zmiany danych.
5. Stara `expected_version` → `409`, brak nadpisania; umowy zachowują dotychczasową regułę.
6. Member/Viewer nie uzyskują prawa PATCH; zapis z błędem audytu wycofuje się.

Done A: regresja przechodzi, frontend nadal wysyła prawidłowy payload, Ruff i quality PASS, commit obejmuje wyłącznie poprawkę i potrzebne testy.

## 4. Etap B — replanning i końcowy kontrakt 013

Pokrycie: R02, R15, R16 oraz przeniesienie dowodów R17.
Zaktualizować `requirements/units/stories/bolt.md/construction-log` w granicach właścicieli AI-DLC; zachować ślad zmiany zakresu.
Propozycja podziału: 013 odpowiada za kompletność roku, lifecycle, dostęp, audit i kontrakt blokady; 014 dowodzi współpracy lifecycle z CRUD przychodu; 015 dowodzi współpracy z plikami; 017 dowodzi integracji przez UI/runtime.
Przenieść kryterium close–income do jawnej story/test checklist 014, zamiast oznaczyć je jako zaliczone w 013.
Powiązać odroczony pomiar okresów z obowiązkowym benchmarkiem 017; wskazać właściciela i warunek końcowego odbioru intentu.
Uzyskać checkpoint replanningu/odbioru 013. Nie zmieniać `complete` ręcznie jako obejścia cyklu zależności.
Formalne zamknięcie wykonuje narzędzie specsmd dopiero po spełnieniu poprawionego zakresu i wymaganej akceptacji.

Kontrakt 013 ma opisywać faktyczny kod, usuwając `proposed` i otwarte kontrole już rozstrzygnięte implementacją:

- UUID zasobów; końcowe `/` w trasach; GET lat = standardowa paginacja 50, GET miesięcy = tablica 12, POST roku = rok z miesiącami.
- `calendar_year`: całkowite `1..9999`; duplikat `409/accounting_period_conflict`; obce lub brakujące obiekty `404`.
- Bieżąca SessionAuthentication: anonimowa próba `403`; brak CSRF/rola zapisu również `403`, z odrębnym opisem przyczyn.
- Blokady `Household → AccountingYear → AccountingMonth` dla obecnego lifecycle; przyszłe mutacje finansowe stosują wspólny kontrakt roku.
- `activated_at` aktualizowany przy activate/reopen, `closed_at` zachowuje ostatnie close; no-op nie zmienia timestamps/audytu.

Pełna macierz zachowania zgodnego z bieżącą regułą target-state:

| Stan wejściowy | activate           | close              | reopen                                     |
| -------------- | ------------------ | ------------------ | ------------------------------------------ |
| inactive       | 200, active, audit | 409, bez zmian     | 409, bez zmian                             |
| active         | 200, no-op         | 200, closed, audit | 200, no-op, nawet bez wcześniejszego close |
| closed         | 409, bez zmian     | 200, no-op         | 200, active, audit                         |

Dodać parametryzowane testy wszystkich dziewięciu komórek, timestamps i liczby audytów.
Zmiana tej semantyki wymaga oddzielnej decyzji; nie poprawiać `reopen(active)` wbrew zaakceptowanej regule.
W schema audytu jawnie opisać obecne object ID miesiąca i lookup roku; propozycja docelowa: również utrwalić `accounting_year_id/calendar_year/month_number` w nowych zdarzeniach dla samowystarczalnego odczytu, bez przepisywania historycznych logów.
Idempotencja stanu nie chroni przed starym close po nowym reopen; rozstrzygnięcie w D4.
Done B: brak cyklu kryteriów odbioru, spójne statusy i końcowy kontrakt potwierdzony testami.

## 5. Etap C — decyzje domenowe i kontrakty 014

Checkpoint 014 ma przedstawić D1–D4 razem z modelem, przykładami API i zmianami stories.
Po zaakceptowaniu odpowiedzi zapisać je w artifacts 014 i decision-index; nie pozostawiać alternatyw w implementowanym kontrakcie.

### D1 — historia przychodu i usuwanie

Rekomendacja: osobny `IncomeRecord` z trwałymi FK do gospodarstwa/miesiąca/źródła i opcjonalnej osoby; `member_id=null` oznacza odbiorcę gospodarstwo.
Przy create utrwalić snapshot: ID/nazwa odbiorcy, ID/nazwa/kind/version źródła, a dla umowy ID/nazwa firmy i dane identyfikujące rodzaj umowy.
Kwota brutto nie jest kwotą przychodu; kopiowanie jej do `amount` zabronione.
Zmiana słownika, przypisania, nazwy firmy/osoby lub konwersja źródła nie zmienia istniejącego snapshotu.
Zmiana kwoty/waluty/daty nie odświeża snapshotu; jawna zmiana odbiorcy/źródła tworzy nowy snapshot i audyt before/after.
Samo ponowne przesłanie tego samego `source_id/member_id` nie jest zmianą powiązania.
Soft delete wpisu: znacznik czasu/wykonawcy i inkrementacja wersji, wpis znika z normalnych list i sum, audit pozostaje.
FK historii chronione przed kaskadowym usunięciem słownika; normalny odczyt historycznego wpisu używa snapshotu, nie bieżących nazw JOIN.
Stare audyty pozostają niezmienne; nie rekonstruować tabeli wersji źródeł z niepełnego logu.

### D2 — kwalifikacja źródła i odbiorcy

Rekomendacja nowego przypisania: aktywna osoba własnego gospodarstwa lub całe gospodarstwo; aktywne źródło tego samego gospodarstwa i dokładnie wybranego odbiorcy.
Dla obu typów źródeł obowiązuje inkluzywne overlap: `start_date <= month_end AND (end_date IS NULL OR end_date >= month_start)`.
Liczy się okres rozliczeniowy, nigdy receipt date.
Archiwalne źródło/osoba nie są dostępne do nowego przypisania, także w dawnym aktywnym miesiącu; wcześniejsze wpisy pozostają czytelne.
Archiwizacja firmy nie wyklucza istniejącej aktywnej umowy; nowe powiązanie umowy z archiwalną firmą nadal zabronione.
`one_off` nie oznacza unikalności przychodu; wiele osobnych wpływów może wskazywać to samo źródło.
Przy edycji kwoty/daty zachować istniejące historyczne relacje; nowe przypisanie walidować regułami powyżej.
Ten sam predykat obsługuje listę wyboru i finalny zapis, ponownie sprawdzany pod blokadami.
Waluta przychodu jest niezależna od waluty źródła; brak automatycznego przeliczania.
Jeśli użytkownik chce dopisywać przychody z archiwalnego źródła za dawny okres, zmienić D2 w checkpointcie i dodać jednoznaczne kryteria, zamiast bocznego wyjątku w kodzie.

### D3 — kwoty i daty

Rekomendacja: decimal `18,2`, API wejściowe/wyjściowe string, zakres rzeczywistej kwoty `0.01..9999999999999999.99`.
Zero i kwoty ujemne odrzucać; korekta istniejącego wpływu przez jawny PATCH/delete, bez nowej domeny ujemnych transakcji.
Więcej niż dwa miejsca po przecinku → `400`, bez zaokrąglania; UI normalizuje przecinek zgodnie z `money.ts`, bez użycia float do obliczeń.
Waluta: zachować bieżący kontrakt trzech wielkich liter; nie obiecywać pełnej walidacji ISO ani szczególnej precyzji JPY/KWD.
Jeśli przyjąć słownik ISO lub różną precyzję walut, najpierw odrębnie zatwierdzić zmianę kontraktu i migracji.
Receipt date: poprawna data kalendarzowa `0001-01-01..9999-12-31`, może leżeć poza miesiącem/rokiem; nie dodawać nieuzgodnionego zakazu przyszłej daty.
Wszystkie ograniczenia backendowe; serializer odrzuca nieznane pola, household/actor/audit nie pochodzą z body.

### D4 — CRUD, wersje i retry

Rekomendacja: nie przenosić wpisu między miesiącami w v1; `month_id` niemutowalne, próba PATCH → `400`.
PATCH: `amount/currency/receipt_date/member_id/source_id` plus obowiązkowe `expected_version`; zmiana zwiększa wersję.
DELETE: soft delete z obowiązkową oczekiwaną wersją; po usunięciu normalny GET/PATCH → `404`.
Ponowienie tego samego delete z kluczem retry może zwrócić zachowany wynik; nowa operacja na usuniętym zasobie → `404`.
Create wymaga `Idempotency-Key` UUID; klucz zakresowany gospodarstwem, aktorem i operacją, utrwalony transakcyjnie z wpisem oraz fingerprintem payloadu.
Ten sam klucz i payload → ten sam wynik/ID, bez kolejnego wpisu/audytu; ten sam klucz z innym payloadem → `409/idempotency_conflict`.
Równoległe retry gwarantuje constraint DB; nie deduplikować po kwocie/dacie/źródle.
Przed zwrotem wyniku retry zawsze ponownie sprawdzić aktualny dostęp; replay create po close zwraca poprzedni wynik bez nowej mutacji.
Nie wprowadzać krótkiego TTL, po którym ten sam klucz nieoczekiwanie utworzy drugi wpływ; retencja klucza co najmniej tak długa jak wpisu.
Propozycja dla lifecycle: `state_version` i `expected_version` sprawdzane przed no-op, aby stary close nie zamknął nowego cyklu; opisać migrację i kompatybilność istniejącego API.
Ta zmiana lifecycle wymaga jawnego zatwierdzenia; jeśli odrzucona, zachować i udokumentować obecne ograniczenie oraz nie twierdzić, że stare retry jest chronione.

### Kontrakt API 014 do zatwierdzenia przed kodem

Proponowane ścieżki pod `/api/households/{household_id}/`, wszystkie z końcowym `/`:

- `accounting-years/{year_id}/months/{month_id}/incomes/`: GET paginowany i POST.
- `accounting-years/{year_id}/months/{month_id}/incomes/{income_id}/`: GET/PATCH/DELETE.
- `accounting-years/{year_id}/months/{month_id}/income-source-options/?member_id={UUID}`; pominięcie member_id oznacza gospodarstwo.
- `accounting-years/{year_id}/months/{month_id}/income-totals/` i `accounting-years/{year_id}/income-totals/`: GET.
  Payload create: `{"member_id":null,"source_id":"UUID","amount":"800.00","currency":"PLN","receipt_date":"2026-09-30"}`.
  Response wpisu: `id, household_id, month_id, member_id, source_id, amount, currency, receipt_date, version, recipient_snapshot, source_snapshot, created_at, updated_at`.
  Listy: `count/next/previous/results`, 50 na stronę; wpisy uporządkowane `receipt_date, created_at, id`; źródła wyboru według `name,id`.
  Totals: `{"totals":[{"currency":"PLN","amount":"800.00"}]}`, waluty alfabetycznie; brak wpisów = `{"totals":[]}`.
  Roczna agregacja po przypisanym miesiącu, nie receipt date; obejmuje wpisy nieusunięte niezależnie od aktywnego/zamkniętego stanu.
  Suma może przekraczać maksimum pojedynczego wpisu; nie zawężać wyniku agregacji do `18,2` pojedynczej pozycji.
  400: shape/fields/amount/source eligibility; 403: sesja/CSRF/brak zapisu; 404: obce/brakujące zasoby; 409: closed/inactive, stale version, retry conflict.
  Stabilne kody domenowe i schema before/after zapisać w technical-design oraz testach; rozszerzyć allowlist audytu dla nowych object types.
  Quick-add korzysta z istniejących endpointów słownika, nie tworzy przychodu automatycznie.

Done C: artifacts 014 zawierają jedną zaakceptowaną odpowiedź na każdą D1–D4, pełne CRUD/eligibility/history/retry stories oraz zatwierdzony kontrakt.

## 6. Etap D — implementacja 014 i dowód kontraktu close–write

Realizować etapami DDD: model → technical design/ADR → implement → test, z checkpointami projektu.
Mutacja: `locked_access` → lock roku → odczyt miesiąca i stanu → walidacja aktualnych powiązań/wersji → zapis wpisu i audit w jednej transakcji.
Nie kopiować kwot konfiguracyjnych, nie używać sygnałów do krytycznego audytu.
Testy PostgreSQL obu wymuszonych kolejności close–create/PATCH/DELETE: wcześniejszy zapis commitował przed close albo późniejszy zapis jest odrzucony.
Testy source reassignment/archive–create, edit–edit, edit–delete, odwołania uprawnień podczas oczekiwania na lock, retry–retry oraz rollback audytu.
Sprawdzić granice liczb/dat, gospodarstwo null-recipient, obce ID każdego zasobu, brak wolnego tekstu, wszystkie role.
Test historii: po zmianie/konwersji/archiwizacji słownika closed month zachowuje poprzednie snapshoty i sumy.
Fixture sum: październik `800 PLN + 200 PLN + 50 EUR` → `1000.00 PLN, 50.00 EUR`; daty wpływu mogą być we wrześniu.
PATCH 200 PLN → 250 PLN daje 1050 PLN; delete 800 PLN daje 250 PLN; roczne sumy wynikają z przypisania okresów.
Done D: migracje, testy kontraktowe/integracyjne, audit i quality PASS; odroczone kryteria 013 mają rzeczywisty dowód w raporcie 014.

## 7. Etap E — decyzje i implementacja 015

Pokrycie R08–R11; checkpoint D5 przed kodem plików.

### D5 — limity, storage i finalizacja

Rekomendowane limity: maks. 10 aktywnych plików/wpis; 10 MiB/plik; 50 MiB łącznie/wpis i w pojedynczym batchu; plik pusty odrzucany.
Formaty PNG/JPEG/PDF sprawdzane z zawartości, nie wyłącznie rozszerzenia/MIME klienta; bez OCR lub zewnętrznego wysyłania dokumentów.
Wybrać konkretny parser walidacji i przypiąć zależność; kontrolować również koszt dekodowania, uszkodzone/złośliwe dane i nazwy ścieżek.
Prywatny storage w trwałym `media_data`, losowe klucze, brak publicznego MEDIA_URL/proxy route; zachować bezpieczną wyświetlaną nazwę osobno.
Create przychodu i upload są oddzielnymi operacjami; błąd uploadu pozostawia poprawnie zapisany przychód i czytelny stan UI.
Batch upload all-or-nothing: staging wszystkich plików poza lockami, następnie finalizacja metadanych/audytu wszystkich plików albo żadnego.
Finalizacja pod `Household → AccountingYear` ponownie sprawdza uprawnienia, stan active, istnienie nieusuniętego przychodu i limity łączne.
Nie wykonywać I/O sieciowego/pliku pod lockiem; dostępność stagingu i stan finalizacji mają jawny protokół odporny na crash.
API udostępnia tylko sfinalizowane metadane; staging bez dowiązania nie jest pobieralny.
Awaria przed commitem usuwa batch lub pozostawia rozpoznawalny staging do cleanup; awaria po commicie nie usuwa plików poprawnego wpisu.
Cleanup co godzinę usuwa niedowiązany staging starszy niż 24 h; działanie idempotentne i udokumentowane dla używanej infrastruktury.
Remove/soft-delete przychodu natychmiast wycofuje autoryzowaną dostępność pliku; fizyczne usuwanie po commicie, z trwałą kolejką cleanup i ponawianiem błędów.
Audit zachowuje metadane operacji, nie bajty dokumentu. Retencję kopii backup ustalić i opisać osobno od dostępności API.
Brak skanera malware nie jest wynikiem „czysty plik”; przed implementacją zatwierdzić brak skanowania albo obowiązkowy skaner z polityką kwarantanny/fail-closed.
Nie instalować usługi skanowania ani zmieniać polityki retencji bez tej decyzji.

Transport: scoped multipart parser endpointu upload; istniejące endpointy pozostają JSON.
Client upload współdzieli session/CSRF/error handling, przesyła FormData bez ręcznego Content-Type/boundary; download zwraca bytes/blob lub autoryzowany link.
Download ustala typ i Content-Disposition, `nosniff`, brak publicznego cache/URL; nie przepuszczać pliku przez JSON helper.
Upload/remove to mutacje: Owner/Admin i active month; wszyscy uprawnieni czytelnicy pobierają również po close.
Obcy tenant/brak zasobu → 404; Member/Viewer write → 403; przekroczenie limitu lub typ → udokumentowany 400/413.
Testy: awaria drugiego pliku, audytu, storage, crash staging/finalizacji/cleanup, concurrent limit, close–attach, delete-income–attach i revoke-access–attach.
Download testować przez porównanie bajtów oraz odmowę dostępu po usunięciu/revocation; restart zachowuje poprawne pliki.
Done E: D5 zatwierdzone, protokół i runbook cleanup opisane, wszystkie failure cases mają jednoznaczny wynik i test.

## 8. Etap F — stories i implementacja UI 016

Pokrycie R05, R10–R14. Rozdzielić Must totals od Should attachments i zapisać, że planowany odbiór 017 obejmuje również pliki.
Nie odraczać Should przez usunięcie obowiązkowych podsumowań.
Checkpoint D6: zaakceptować konkretne przepływy new/edit/delete/quick-add/upload failure i ich stany.
Przed nowymi ekranami: plan → wizualizacja → osobny niezależny subagent → Score >7,5/10 → jawna akceptacja właściwej wersji → kod.
Nie utożsamiać akceptacji tego planu z akceptacją wizualizacji.

Implementacja:

- Współdzielić formularze źródeł/umów; callback zwraca utworzony obiekt/ID, bez kopiowania istniejącej logiki.
- Quick-add zachowuje household/year/month/recipient i draft kwoty/waluty/daty; po sukcesie wybiera nowe kwalifikujące się źródło.
- Anulowanie quick-add nie usuwa wpisanych danych; zapis słownika nie zapisuje przychodu.
- Zmiana odbiorcy czyści niepasujące źródło, abortuje/ignoruje stare odpowiedzi i nie dopuszcza źródła poprzedniej osoby.
- Nie przekształcać udanego create w drugi create przy błędzie samego uploadu; retry korzysta z właściwego klucza operacji.
- Create nie wypełnia rzeczywistej kwoty brutto/podpowiedzią; edit pokazuje zapisaną kwotę i historyczne etykiety.
- PATCH używa aktualnej wersji, konflikt zachowuje draft i pozwala jawnie odświeżyć; delete wymaga czytelnego potwierdzenia.
- Rozszerzyć allowlist błędów w `api.ts`: calendar_year, amount, receipt_date, source_id, wersja, pola uploadu.
- State conflict odświeża stan z serwera; formularz inactive/closed i kontrolki Member/Viewer nie oferują mutacji.
- Must totals pozostają widoczne dla czytelników i closed periods; puste = jawny stan bez wpisów.
- Preview/download korzysta wyłącznie z prywatnego transportu; komunikat części operacji nie sugeruje, że nieudane pliki zapisano.
- Zamiana gospodarstwa czyści kontekst poprzedniego; brak spóźnionych danych i ID w nowym formularzu.

Done F: zaakceptowane wizualizacje, testy browser/API dla create/edit/delete/quick-add/retry/permissions, responsive/accessibility, quality PASS.

## 9. Etap G — odbiór 017 i wydajność

Przygotować deterministyczny harness z osobnymi syntetycznymi gospodarstwami A/B i czterema rolami; nie używać danych produkcyjnych.
Macierz: role × read/create/PATCH/DELETE/activate/close/reopen/upload/remove/download, stany inactive/active/closed i mieszane ID A/B.
Owner/Admin zapisują w active; Member/Viewer odczytują i pobierają, nigdy nie zapisują; obcy tenant nie uzyskuje danych.
Włączyć wszystkie testy D/E, historyczne snapshoty, sumy po CRUD, daty poza rokiem i oddzielne waluty.
Restart rzeczywistych usług z trwałym DB/storage, następnie odczyt stanu/kwot/snapshotów/bajtów oraz sum; restart samej mockowanej przeglądarki nie wystarcza.
Dowód przypadku: fixture, kroki, expected, actual, identyfikator testu/komenda, commit i wynik; brak pomiaru = niezweryfikowane.

Proponowany benchmark P95 do zatwierdzenia w planie odbioru:

- Osobny runtime Postgres, bez finansów użytkownika; 10 gospodarstw, po 10 lat/120 miesięcy, po 100 wpisów w każdym miesiącu.
- Endpointy: list/create year, list months, activate/close/reopen, list/create/PATCH/delete income, month/year totals, source-options.
- 50 żądań warm-up i 200 pomiarowych na endpoint, concurrency 1 oraz 5; unikalne dane i klucze dla mutacji.
- Czas klienta HTTP do API przez proxy, z uwierzytelnioną sesją; mierzyć z jednoznacznie zapisanym sposobem CSRF, bez kosztu logowania per próbka.
- Raportować liczbę żądań, odsetek błędów, medianę, P95, wersje usług/hardware/dane; błędów nie wycinać po cichu z próby.
- Cel P95 <500 ms dla podstawowych operacji API; transfer całych plików raportować oddzielnie, bez utożsamienia z tym samym SLA.
- Jeśli cel nieosiągnięty, wskazać endpoint/przyczynę/poprawkę i powtórzyć tylko potrzebny pomiar; nie deklarować PASS przy niezmierzonym celu.

Done G: obie acceptance stories mają pełny raport i dowody; statusy specsmd dopiero po checkpointcie i oficjalnym zamknięciu.

## 10. Śledzenie ustaleń i warunki oddania

| Review | Etap  | Minimalny dowód zamknięcia                                                       |
| ------ | ----- | -------------------------------------------------------------------------------- |
| R01    | A     | Pełny PATCH zachowuje archiwalnego właściciela; nowe przypisanie jest odrzucane. |
| R02    | B     | Odroczone kryteria mają właściciela w 014/017, bez cyklu odbioru.                |
| R03    | C/D   | D1 i test historii po zmianie/konwersji/archive.                                 |
| R04    | C/D   | D2, wspólny predykat i testy granic/race.                                        |
| R05    | C/D/F | D4, udane edit/delete oraz sumy, wersje i UI.                                    |
| R06    | C/D/F | Utracona odpowiedź + retry daje jeden wpis/audyt.                                |
| R07    | C/D   | D3 i testy granic serializerów bez silent rounding.                              |
| R08    | E     | Finalizacja pod lockiem i obie kolejności close–attach.                          |
| R09    | E     | D5, crash/failure/cleanup/storage po restarcie.                                  |
| R10    | E/F   | Multipart i autoryzowany download zachowują bajty.                               |
| R11    | E/G   | Member/Viewer download PASS, upload/remove DENIED.                               |
| R12    | F     | Must totals osobno od opcjonalności plików.                                      |
| R13    | F     | Quick-add wraca z ID i draftem, bez stale source.                                |
| R14    | C/F   | Zatwierdzone JSON/error schemas i field errors UI.                               |
| R15    | B/C   | Wszystkie 9 wyników lifecycle i jawna decyzja stale retry.                       |
| R16    | B     | Dokumentacja dokładnie odpowiada trasom/auth/audit.                              |
| R17    | G     | Macierz dowodów, trwałość i mierzalny P95.                                       |

Po każdej zmianie kodu format/lint zgodnie z językiem; nie wyłączać reguł, nie formatować dependencies/dystrybucji specsmd.
Przed oddaniem etapu: przegląd diff/duplikacji/odpowiedzialności, `scripts/quality.ps1`, testy zakresu, migracje `--check --dry-run`, jeśli zmieniono modele.
Nie deklarować końca na podstawie samego coverage lub raportu innego agenta; sprawdzić aktualne pliki i wyniki.
Finalny raport implementatora: R01–R17 z commitami i dowodami, decyzje zaakceptowane/oczekujące, branche/statusy boltów, pozostałe ograniczenia.
Całość ukończona dopiero, gdy żadna R-pozycja nie opiera się na otwartej alternatywie lub brakującym dowodzie, a formalne checkpointy zostały spełnione.
