# Review incomes, periods i planów boltów 013–017

Data: 2026-10-07. Przegląd kodu i dokumentacji z commita `3188a69`, na bazie `feat/bolt-013-periods-api`. Raport powstaje na osobnym branchu `docs/task-review-incomes-periods-013-017`, z tej bazy, ponieważ obejmuje jeszcze niescalony kod 013 i jego zatwierdzone plany. Przed utworzeniem brancha pobrano referencje `origin`; zastany katalog roboczy był czysty.

Największe ryzyko dla słabszego modelu to konieczność wymyślenia zasad historii, dostępności źródeł, edycji/usuwania i zapisu plików. W bolcie 013 kontrakt blokowania jest już konkretny, ale kryteria jego ukończenia zależą od następnego bolta. W istniejącym kodzie potwierdzono też błąd edycji innego źródła po archiwizacji jego właściciela.

## Zakres i znaczenie ocen

Przeczytano modele i migracje gospodarstw, serwisy/widoki/serializery źródeł, umów i okresów, politykę dostępu, audyt, testy API/współbieżności, formularze źródeł i umów, klienta HTTP oraz konwencje kwot frontendu. Przejrzano wymagania i kontekst intentu 003, wszystkie cztery unit briefs i 15 stories, pięć boltów, model/projekt/ADR/test report 013 oraz powiązane wymagania intentu 002 i standardy projektu.

`IncomeSource` to konfiguracja źródła dochodu. Na badanym commicie nie ma jeszcze modelu/API rzeczywistych przychodów ani ich załączników; 014–017 mają status `planned`, a 013 jest na etapie `test`. Brak tych implementacji nie jest zgłaszany jako błąd.

- **Błąd kodu**: istniejąca ścieżka ma wykazane niepoprawne zachowanie.
- **Sprzeczność**: dwa obowiązujące opisy lub opis i kod prowadzą do różnych wyników.
- **Luka planu**: decyzja nie jest ustalona. Nie oznacza błędu działającej aplikacji, ale przed implementacją trzeba zamknąć ją w zatwierdzonym projekcie.
- **P1**: ryzyko integralności finansów, autoryzacji lub blokady realizacji planu; **P2**: istotna niejednoznaczność kontraktu, UX lub odbioru.

Odroczenie decyzji do Construction jest prawidłowe dla planu Inception. Problemem jest brak konkretnej odpowiedzi i sprawdzalnej bramki, która uniemożliwi implementację na podstawie domysłu. Poniższe propozycje są rekomendacjami review, nie nowymi zatwierdzonymi wymaganiami.

## Ustalenia

### R01 — P2, błąd kodu: niezmienione przypisanie do archiwalnej osoby blokuje edycję źródła

**Dowód:** [record_services.py](../../backend/households/record_services.py), linie 59–81 i 146; [other-sources-panel.tsx](../../frontend/app/components/other-sources-panel.tsx), linie 43–45, 64 i 102–106. Komentarz serwisu mówi, że tylko nowo przypisane relacje muszą być aktywne. Walidator sprawdza jednak każdy niepusty `member_id` przesłany w PATCH. Formularz zawsze go wysyła i udostępnia archiwalnego właściciela jako zachowywalną opcję.

**Odtworzenie:** utworzyć inne źródło dla osoby, zarchiwizować osobę, zmienić tylko nazwę źródła, zachowując `member_id` i aktualne `expected_version`. API zwraca `400 member_id`. Ten sam PATCH z pominiętym `member_id` zwraca `200`. Edycja umowy z identycznym archiwalnym właścicielem zwraca `200`, ponieważ [family_income_services.py](../../backend/households/family_income_services.py), linie 157–167, odróżnia zachowanie relacji od nowego przypisania. Wszystkie trzy wyniki potwierdzono na osobnej bazie testowej.

**Do doprecyzowania/poprawy:** wspólna zasada „istniejącą relację można zachować; nowe przypisanie wymaga aktywnego obiektu z tego gospodarstwa”. Test musi przejść przez payload rzeczywistego formularza. Nie naprawiać przez wyzerowanie właściciela ani przepięcie źródła na gospodarstwo. Dotyczy obecnego słownika i jego ponownego użycia w 014/016.

### R02 — P1, sprzeczność planu: ukończenie 013 czeka na bolt, który wymaga 013

**Dowód:** [story close-and-reopen](../../memory-bank/intents/003-budget-periods-and-income/units/001-periods-api/stories/003-close-and-reopen-month.md), linie 24–25; [test report 013](../../memory-bank/bolts/013-periods-api/ddd-03-test-report.md), linie 31, 67–80; [bolt 014](../../memory-bank/bolts/014-monthly-income-api/bolt.md), `requires_bolts` i sekcja Requires. Raport 013 pozostawia niezrealizowane kryterium zapisu przychodu i czeka z pełnym odbiorem na 014. Plan 014 wymaga 013. To cykl kryteriów odbioru, choć sam graf `requires_bolts` nie zawiera cyklu.

**Ryzyko domysłu:** model albo nie ruszy 014, albo uzna 013 i całe story za ukończone bez dowodu. Skrypt zamykający bolt oznacza wszystkie jego stories jako zaimplementowane.

**Do doprecyzowania:** rozdzielić odbiór lokalnego lifecycle/kontraktu blokady 013 od obowiązkowego testu integracyjnego w 014 i końcowego odbioru 017. Zapisać dokładnie, kto jest właścicielem odroczonego kryterium i czy wolno rozpocząć 014 przy obecnym statusie 013. Replanning wymaga jawnego zapisu decyzji; nie wystarczy komentarz w raporcie testów.

### R03 — P1, luka planu: stabilny ID i audyt słownika nie definiują historycznego obrazu przychodu

**Dowód:** [bolt 014](../../memory-bank/bolts/014-monthly-income-api/bolt.md), linia 83; [unit monthly-income](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/unit-brief.md), linia 30; [story select-source](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/002-select-dictionary-source.md), linie 28, 32 i 48. Obecne serwisy pozwalają zmieniać nazwę, właściciela, daty i typ źródła, w tym konwertować `other` w `contract` z zachowaniem ID. `income_snapshot()` jest snapshotem audytu źródła, nie jeszcze snapshotem przyszłego przychodu. Audyt innych źródeł nie zawiera `kind/version`, a kontraktów je zawiera.

**Ryzyko domysłu:** odczyt starego, nawet zamkniętego miesiąca przez JOIN do bieżącego słownika pokaże nową nazwę/osobę/typ. Sam `source_id` albo samo `source.version` nie rozstrzygają, skąd pobrać dawną reprezentację; brak osobnej tabeli wersji źródła.

**Do doprecyzowania przed 014:** zatwierdzić snapshot lub wersjonowanie i dokładną listę pól: co najmniej tożsamości, nazwy odbiorcy/źródła, typu oraz ewentualnie firmy/warunków umowy. Określić, kiedy snapshot powstaje, które edycje go odświeżają i co wyświetla historyczny odczyt. Test: zapisać przychód, zamknąć miesiąc, zmienić nazwę/przypisanie źródła, skonwertować lub zarchiwizować źródło/osobę; wynik odczytu ma konkretne oczekiwane wartości, a suma pozostaje taka sama. Wersjonowanie przez rekonstrukcję audytu wymaga osobnego kompletnego kontraktu, nie założenia, że log jest tabelą wersji.

### R04 — P1, luka planu: „eligible sources” nie jest kompletnym predykatem backendu

**Dowód:** [story select-source](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/002-select-dictionary-source.md), linie 23–25, 32 i 48; [ContractListView](../../backend/households/family_income_views.py), linie 96–109; [RecordListView](../../backend/households/record_views.py), linie 32–34 i 55–58. Opis zawiera inkluzywne nakładanie dat umowy z miesiącem, ale obecne listy słownika nie realizują wyboru dla miesiąca. Umowy mają filtr osoby, bez filtra okresu/aktywności; lista źródeł jest ogólną listą gospodarstwa.

**Brak odpowiedzi:** czy nakładanie dat obowiązuje także inne źródła; czy archiwalna umowa jest dopuszczalna dla wcześniejszego miesiąca; czy archiwizacja osoby lub firmy blokuje nowe użycie historycznie obowiązującej umowy; czy `one_off` można użyć wielokrotnie; czy waluta wpisu może różnić się od waluty źródła. Data otrzymania jest niezależna od miesiąca — nie może przypadkowo zastąpić okresu w filtrze umów.

**Do doprecyzowania:** jedna tabela kwalifikacji dla `contract/other`, osoba/gospodarstwo, statusy i daty, egzekwowana identycznie przy listowaniu i zapisie. Wskazać endpoint wyboru albo dokładne filtry istniejącego API. Nowy POST/PATCH ponownie waliduje źródło po uzyskaniu blokad; filtr frontendowy nie jest zabezpieczeniem. Testy obejmują granice dat, archiwizację/reassignment pomiędzy odczytem opcji a zapisem i złośliwe ID spoza listy.

### R05 — P1, luka planu: edycja i usuwanie są w zakresie bez pełnych pozytywnych kryteriów

**Dowód:** [unit monthly-income](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/unit-brief.md), linia 24; [story record-income](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/001-record-income.md), linie 23–32; [story enter-details](../../memory-bank/intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/004-enter-income-details.md), linie 23–27. Stories opisują udany create i odmowę edit/delete dla czytelnika; nie określają udanej edycji/usunięcia przez Owner/Admin ani pełnego przepływu UI.

**Ryzyko domysłu:** implementacja tylko POST spełni większość checklist. Albo model pozwoli przenieść wpis z zamkniętego miesiąca, sprawdzając jedynie aktywność docelowego. Brak reguły konfliktu równoległych edycji i skutków usunięcia dla audytu/plików/sum.

**Do doprecyzowania:** dozwolone pola PATCH, możliwość zmiany odbiorcy/źródła/miesiąca, soft/hard delete, odpowiedzi i ponowienie DELETE, token wersji lub świadoma polityka ostatniego zapisu. Jeśli przenoszenie jest dozwolone, oba okresy muszą spełniać politykę edycji; ustalić kolejność blokad obu lat zgodną z ADR-006. Jeśli zabronione — jawnie odrzucać zmianę miesiąca. Dodać kryteria UI edycji/usuwania oraz testy sum i audytu przed/po każdej mutacji, wyścigu edit–edit, edit–delete i close–write.

### R06 — P1, luka planu: retry po timeout może podwoić rzeczywisty przychód

**Dowód:** [story record-income](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/001-record-income.md), linia 49: identyczne wpisy są odrębne „unless an explicit idempotency key identifies a retry”; [story enter-details](../../memory-bank/intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/004-enter-income-details.md), linia 47: zachować formularz i umożliwić retry; [api.ts](../../frontend/app/lib/api.ts), linie 204–225: klient kończy oczekiwanie po 15 sekundach, co nie dowodzi rollbacku serwera.

**Ryzyko domysłu:** pierwszy zapis commitował, odpowiedź zginęła, użytkownik ponawia i suma rośnie dwa razy. Dedup po kwocie/dacie/źródle byłby sprzeczny z wymaganiem wielu odrębnych wpływów.

**Do doprecyzowania:** zdecydować, czy klucz retry jest wymagany; jeśli tak, opisać zakres, trwałość, unikalność, równoległe żądania, ten sam klucz z innym payloadem oraz ponowienie po zamknięciu miesiąca. UI zachowuje klucz dla retry tej samej operacji i zmienia go dla nowego wpływu. Test: utracona odpowiedź po commicie + retry = jeden wpis i jeden audyt, dwa świadome wpływy = dwa wpisy.

### R07 — P2, luka planu: „valid amount/currency/date” pozostawia decyzje finansowe do zgadywania

**Dowód:** [story amount-currency-date](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/003-record-amount-currency-date.md), linie 23, 26, 31 i 47; [record_serializers.py](../../backend/households/record_serializers.py), `IncomeInput/ContractInput`; [money.ts](../../frontend/app/lib/money.ts). Istniejące kwoty konfiguracji mają `18,2`, minimum zero, a waluta jest sprawdzana tylko regexem trzech wielkich liter. Nie wynika z tego automatycznie, że rzeczywisty przychód ma akceptować zero, dowolne trzy litery i wszystkie daty przyszłe.

**Do doprecyzowania:** precyzja i maksimum kwoty, zero/ujemne korekty, odrzucanie nadmiarowych miejsc dziesiętnych, format string w JSON, normalizacja przecinka w UI, lista walut i relacja do waluty źródła, dopuszczalny zakres dat/future dates. Jawnie rozstrzygnąć waluty z inną liczbą miejsc dziesiętnych, jeśli mają być obsługiwane. Zapisać tabelę payload → wynik dla wartości granicznych i błędnych. Odesłanie „reuse conventions” nie zastępuje tych decyzji biznesowych.

### R08 — P1, luka planu: blokada zamkniętego miesiąca nie ma kontraktu dla mutacji załączników

**Dowód:** [ADR-006](../../memory-bank/bolts/013-periods-api/adr-006-accounting-year-lock-for-financial-writes.md), Decision: blokady `Household → AccountingYear`, transakcje bazodanowe bez I/O plikowego; [story attachments](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/005-private-income-attachments.md), linie 23–31 i 48; [UI attachments](../../memory-bank/intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/005-manage-attachments-and-totals.md), linia 27: zamknięty miesiąc pozostaje tylko do odczytu.

**Ryzyko domysłu:** upload/remove nie sprawdzi stanu okresu, bo nie zmienia kwoty. Albo stan zostanie sprawdzony przed długim uploadem i zamknięcie nastąpi przed przypięciem pliku. Trzymanie blokady podczas I/O naruszy ADR.

**Do doprecyzowania przed 015:** upload/usunięcie/zastąpienie pliku traktować według jawnej polityki mutacji okresu, oddzielając staging pliku od krótkiego finalizującego zapisu metadanych i audytu. W finalizacji ponownie sprawdzić uprawnienia, istnienie wpisu i stan miesiąca pod uzgodnionymi blokadami. Odrzucenie po uploadzie wymaga bezpiecznego cleanup. Testy obu kolejności close–attach, delete-income–attach i revoke-access–attach oraz read-only pobrania po zamknięciu.

### R09 — P2, luka planu: atomicity i private storage to cele bez rozstrzygniętego przepływu

**Dowód:** [bolt 015](../../memory-bank/bolts/015-income-attachments-api/bolt.md), linie 65–72; [story attachments](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/005-private-income-attachments.md), linie 27, 31 i 48; [compose.yaml](../../compose.yaml), wolumen `media_data`; [settings.py](../../backend/config/settings.py), linia 56. Jest katalog i wolumen media, ale jeszcze brak modelu/storage/API załączników. To nie dowodzi istnienia gotowego prywatnego przepływu z kontekstu intentu.

**Brak odpowiedzi:** czy wpis+pliki zapisują się razem, czy wpis najpierw; przy awarii drugiego pliku wszystko się wycofuje czy pierwszy pozostaje; limity na plik/wpis/request; retencja po usunięciu; miejsce kwarantanny; polityka błędu/braku skanera; cleanup po awarii procesu, nie tylko obsłużonym wyjątku.

**Do doprecyzowania:** przed kodem 015 zapisać liczby i jednoznaczną tabelę rezultatów: błędny typ, limit, awaria zapisu, awaria audytu, brak miejsca, przerwany upload, awaria cleanup. Baza i filesystem nie stanowią jednej transakcji Django; określić kompensację/reconciliation oraz trwałe storage i backup. Ustalić walidację zawartości, bezpieczne nazwy i nagłówki pobrania oraz brak publicznej ścieżki. To decyzje projektowe, a nie pretekst do instalowania nieuzgodnionych usług.

### R10 — P2, luka integracyjna: obecny klient HTTP i parser obsługują tylko JSON

**Dowód:** [api.ts](../../frontend/app/lib/api.ts), linie 192–225: `Content-Type: application/json`, `JSON.stringify`, odczyt `response.json()`; [settings.py](../../backend/config/settings.py), linia 87: tylko `JSONParser`; [story UI attachments](../../memory-bank/intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/005-manage-attachments-and-totals.md), linie 24–26.

**Ryzyko domysłu:** ponowne użycie `api()` z `File/FormData` nie prześle binariów; pobranie PDF przez ten helper nie zwróci pliku. Globalna zmiana parserów może rozszerzyć istniejące kontrakty bez potrzeby.

**Do doprecyzowania 015/016:** multipart lub inny jawny upload contract, parser tylko we właściwym endpointcie, wspólna obsługa świeżego CSRF/session/timeout/error bez duplikowania logiki. Dla multipart nie wpisywać ręcznie boundary. Pobranie: uwierzytelniony link albo helper zwracający blob, z nazwą i typem pliku. Testować przesłane bajty oraz pobrane bajty, nie sam `200`.

### R11 — P2, sprzeczność: acceptance może zabronić czytelnikom legalnego pobierania plików

**Dowód:** [story acceptance income-journey](../../memory-bank/intents/003-budget-periods-and-income/units/004-periods-income-acceptance/stories/002-income-journey-attachments.md), linia 27: „Given Member/Viewer ... when access or upload is attempted ... failure”; [system-context](../../memory-bank/intents/003-budget-periods-and-income/system-context.md), diagram relacji czytelnika: odczyt wpisów i dostępnych załączników; [unit monthly-income](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/unit-brief.md), linia 24: ograniczenie dotyczy zapisu.

**Do doprecyzowania:** rozbić scenariusz na role × operacje. Member/Viewer własnego gospodarstwa: odczyt i download dozwolone zgodnie z polityką wpisu; create/edit/delete/upload/remove zabronione. Obcy tenant i użytkownik bez sesji: osobne przypadki odmowy. Test acceptance nie może traktować zgodnego odczytu jako naruszenia.

### R12 — P2, sprzeczność priorytetów: obowiązkowe podsumowania UI są schowane w Should

**Dowód:** [requirements](../../memory-bank/intents/003-budget-periods-and-income/requirements.md), FR-08 ma `Must`; [story UI attachments-and-totals](../../memory-bank/intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/005-manage-attachments-and-totals.md), linie 6, 10 i 23, łączy podsumowania FR-08 z opcjonalnymi plikami FR-06 jako `Should`. Bolt 016 powiela ten priorytet.

**Ryzyko domysłu:** model odłoży całą story jako opcjonalną i nie pokaże wymaganych sum. Jednocześnie 015 jest obowiązkową zależnością UI i acceptance mimo `Should` FR-06.

**Do doprecyzowania:** rozdzielić Must summaries od Should attachments albo jawnie ustanowić obowiązkowość pełnego zakresu tego wydania. Jeśli Should nie podlega odroczeniu w tym planie, zapisać to w kryteriach i zależnościach; nie pozostawiać sprzecznych sygnałów.

### R13 — P2, luka planu: szybkie dodanie źródła nie określa powrotu do formularza przychodu

**Dowód:** [story UI recipient-source](../../memory-bank/intents/003-budget-periods-and-income/units/003-periods-income-ui/stories/003-add-income-recipient-source.md), linie 26, 32 i 49; [ContractForm](../../frontend/app/components/contract-form.tsx) oraz `OtherSourceForm` w [other-sources-panel.tsx](../../frontend/app/components/other-sources-panel.tsx). Istniejące formularze wykonują własne requesty i zwracają callback `onSaved()` bez utworzonego obiektu/ID; formularz innych źródeł jest lokalny dla swojego panelu.

**Ryzyko domysłu:** kopiowanie formularza lub wyjście do zarządzania rodziną gubi odbiorcę/miesiąc/kwotę/pliki. API może utworzyć źródło, ale UI nie wie, którą pozycję automatycznie wybrać. Zmiana odbiorcy może pozostawić wybrane źródło poprzedniej osoby albo spóźnioną odpowiedź listy opcji.

**Do doprecyzowania 016:** ustalić sposób współdzielenia formularzy i kontrakt zwracania ID/obiektu, prefill odbiorcy, zakres zachowywanego draftu, anulowanie oraz awarię po zapisie źródła. Nie cofać poprawnie utworzonego źródła bez jawnej polityki. Zmiana odbiorcy czyści niepasujące źródło i ignoruje stare odpowiedzi. Test pełnego round-trip quick-add oraz zmiany odbiorcy podczas ładowania.

### R14 — P2, luka planu: brak ustalonego kontraktu odpowiedzi, sum i błędów dla 014–016

**Dowód:** [story totals](../../memory-bank/intents/003-budget-periods-and-income/units/002-monthly-income-api/stories/004-period-totals-by-currency.md), linie 31 i 46: „zero or no summary”; [api.ts](../../frontend/app/lib/api.ts), `errorFromResponse()` ma allowlist pól bez `calendar_year` i przyszłych pól przychodu/pliku. Obecne API okresów zwraca paginowaną listę lat, zwykłą tablicę miesięcy i pełny obiekt roku przy tworzeniu; sama nazwa `list` nie przesądza formatu.

**Do doprecyzowania:** w projekcie 014 zapisać request/response examples dla CRUD, opcji źródeł i sum; nazwy pól, UUID/null odbiorcy gospodarstwa, pagination/order/filtering, puste sumy, kolejność walut i string decimal. Roczne sumy wynikają z przypisanego roku miesiąca, nie roku receipt date; uwzględniają dozwolone zapisane wpisy także w zamkniętych miesiącach i wykluczają usunięte według ustalonej polityki. Ustalić kody 400/403/404/409 i pola audytu. 016 musi rozszerzyć mapowanie walidacji w kliencie, aby błędy nowych pól trafiały pod właściwe kontrolki. Testy przykładowych JSON powinny być wspólne dla konsumenta i API.

### R15 — P2, niejednoznaczny kontrakt 013: tabela stanów nie pokazuje wszystkich odpowiedzi

**Dowód:** [technical design 013](../../memory-bank/bolts/013-periods-api/ddd-02-technical-design.md), linie 54–62 i 114; [period_services.py](../../backend/households/period_services.py), linie 73–76. Idempotencję wyznacza wyłącznie zgodność stanu docelowego, nie tożsamość poprzedniego żądania. Odtworzenie: activate świeżego miesiąca, następnie reopen bez wcześniejszego close → `200`, `closed_at=null`, brak nowego audytu. Jest to zgodne z regułą target-state, ale łatwe do błędnego wywnioskowania z tabeli „tylko trzy przejścia”.

**Ryzyko domysłu:** nowy test lub frontend będzie oczekiwać `409` dla tego przypadku. Opóźnione ponowienie close po poprawnym reopen zamknie następny cykl — obecna idempotencja nie chroni przed takim starym żądaniem.

**Do doprecyzowania:** publikować pełną macierz 3 stany × 3 akcje z kodem, zmianą timestampów i liczbą audytów; jawnie potwierdzić `reopen(active)` jako no-op lub zmienić kontrakt. Osobno rozstrzygnąć, czy stale request po nowym cyklu wymaga tokena wersji. Nie przedstawiać bieżącego zachowania jako odstępstwa od przyjętej reguły target-state.

### R16 — P2, rozjazd dokumentacji 013 z implementacją: publiczny kontrakt nadal jest „proposed”

**Dowód:** [technical design 013](../../memory-bank/bolts/013-periods-api/ddd-02-technical-design.md), linie 16, 28, 35–37, 83, 92 i 122–124; [urls.py](../../backend/households/urls.py), trasy przejść mają końcowy `/`; [settings.py](../../backend/config/settings.py), SessionAuthentication; [test_family_income_api.py](../../backend/households/tests/test_family_income_api.py), linie 373–375, anonimowy odczyt zwraca `403`, nie ogólne `401` z projektu. Audyt przejścia zawiera ID miesiąca i before/after state; rok/klucz kalendarzowy wymaga dołączenia danych miesiąca, choć projekt wymienia identity roku/miesiąca w payloadzie.

**Do doprecyzowania po Stage 4:** zamienić propozycję na kontrakt zgodny z kodem: dokładne trasy ze slash, serializery/kształty odpowiedzi, rzeczywiste kody sesji/CSRF/tenant isolation, `accounting_period_conflict`, semantyka timestampów i schema audytu. Ustalić, czy audyt ma być samowystarczalny z kluczem roku/miesiąca, czy świadomie opiera się na trwałym FK-look-up. Brak tych pól nie oznacza sam w sobie braku audytu; oznacza niedoprecyzowany kontrakt konsumenta i rozjazd z opisem.

### R17 — P2, luka odbioru 017: brak konkretnej macierzy dowodów i warunków P95

**Dowód:** [bolt 017](../../memory-bank/bolts/017-periods-income-acceptance/bolt.md), linie 64–69; obie [stories acceptance](../../memory-bank/intents/003-budget-periods-and-income/units/004-periods-income-acceptance/unit-brief.md); [test report 013](../../memory-bank/bolts/013-periods-api/ddd-03-test-report.md), linie 54–80. Opisuje się ogólne role, restart i źródła, lecz nie wskazuje pełnych przypadków CRUD/retry/wyścigów i mierzalnego planu P95. Raport 013 uczciwie stwierdza, że P95 nie zmierzono; nie wolno później zinterpretować jego wyniku jako potwierdzenia wydajności.

**Do doprecyzowania:** tabela wymaganie → fixture → kroki → dokładny wynik → dowód. Co najmniej wszystkie role dla każdej operacji, dwa gospodarstwa i mieszane ID, mutacje przy active/inactive/closed, granice dat źródeł, historia po zmianie słownika, retry po utracie odpowiedzi, rollback audytu, wyścigi z close, awarie uploadu i restart z rzeczywistym trwałym wolumenem. PostgreSQL jest wymagany dla dowodu blokad; SQLite/mocked response nie zastępują testu konkurencji. Ustalić endpointy P95, dane, liczbę próbek, współbieżność, warm-up i to, czy mierzony jest API server czy pełna ścieżka przeglądarki. Brak dostępu do środowiska oznacza „niezweryfikowane”, a nie PASS.

## Kolejność domknięcia

| Etap                                | Co musi zostać rozstrzygnięte                             | Oczekiwany dowód                                                                                                                              |
| ----------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Przed zamknięciem 013 / startem 014 | R02, R15–R16                                              | Zapisany podział kryteriów odbioru; końcowy kontrakt API i macierz stanów zgodne z kodem.                                                     |
| Przed kodem 014                     | R03–R07, R14                                              | Zatwierdzony model historii, tabela kwalifikacji, pełny CRUD/retry/kwoty i przykłady JSON; testy blokad wspólnie z 013.                       |
| Przed kodem 015                     | R08–R10 i R11                                             | Protokół finalizacji plików, konkretne limity/storage/cleanup, transport i macierz uprawnień; zgodność z ADR-006.                             |
| Przed kodem 016                     | R01 jako zależność słownika, R05, R12–R14                 | Gotowe wspólne formularze/kontrakty; udane edit/delete/quick-add; Must totals; wymagana bramka UI z niezależną oceną >7,5 i jawną akceptacją. |
| Przed odbiorem 017                  | R11 i R17 oraz kryteria wszystkich wcześniejszych ustaleń | Powtarzalna macierz testów z dowodami, konkretne sumy i zachowanie historii, pomiar lub jawna blokada P95.                                    |

Praktyczna zasada dla słabszego modelu: każde „eligible”, „valid”, „according to policy”, „all-or-partial”, „during design” ma wskazywać jedną zatwierdzoną regułę oraz test. Jeżeli decyzja pozostaje otwarta, projekt może być planowany, ale jego odpowiednia część nie jest gotowa do implementacji.

## Weryfikacja tego review

- Ponownie uruchomiono 20 testów: `test_periods_api`, `test_periods_concurrency`, `test_family_income_api`, `test_family_income_concurrency`. Wynik **20/20 PASS** na osobnej testowej bazie PostgreSQL, z aktualnym backendem zamontowanym read-only do jednorazowego kontenera.
- Niezależne odtworzenie R01: `400` z niezmienionym archiwalnym `member_id`, `200` z pominiętym polem, `200` dla analogicznej edycji umowy. Odtworzenie R15: `reopen(active)` bez wcześniejszego close daje `200`, `closed_at=null`. Użyto danych syntetycznych i osobnej bazy, usuniętej po próbie.
- `scripts/quality.ps1`: **PASS** — Ruff format/check, Prettier, ESLint, Stylelint i TypeScript. Sam raport sformatowano Prettierem; sprawdzono wszystkie 50 odnośników do źródeł (brak nieistniejących plików).
- Nie odtworzono wcześniejszego pomiaru 99% coverage ani wszystkich 91 testów; to dane istniejącego raportu 013. Wynik 20/20 nie dowodzi poprawności planowanych boltów 014–017, testów browser E2E ani P95.
- Raport nie zmienia kodu aplikacji, zatwierdzonych decyzji domenowych ani statusów boltów. Rozstrzygnięcia biznesowe i naprawa R01 pozostają kolejnym zakresem pracy.
