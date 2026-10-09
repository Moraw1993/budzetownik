---
artifact: independent-implementation-review
bolt: 016-periods-income-ui
design: sidebar-v3
reviewer: /root/review_ui016_final
previous_reviewer: /root/review_ui016
reviewed_at: "2026-10-09T15:25:27+02:00"
decision: accepted
score: 8.3
scope: code-review-api-contract-and-independent-render-review
code_commit: 3c0d1b5
render_decision: accepted
render_score_range: 8.4-8.5
test_stage: pending
---

# Niezależny przegląd implementacji bolta 016

**accepted, Score 8,3/10** dla przeglądu kodu i zgodności API w poniższym snapshotcie. Po poprawkach autora nie pozostają otwarte P1/P2 w tym przeglądzie. **Nie jest to E2E PASS, zamknięcie Test ani bolta.** Końcowy snapshot kodu: commit 3c0d1b5. Niezależnie obejrzano 18 rzeczywistych renderów implementacji; wynik accepted, Score 8,4–8,5/10. Build, quality oraz Playwright podano oddzielnie jako wyniki rodzica; Test/017 pozostają otwarte.

Pierwszy recenzent /root/review_ui016 oraz domykający recenzent /root/review_ui016_final są osobnymi subagentami, nie autorami kodu. Użytkownik zaakceptował sidebar-v3 i rozpoczęcie implementacji — recenzja kodu odnosi się do tego zatwierdzonego planu. Brak zmian kodu lub commitów recenzenta. Raportowano tylko do delegującego parent; nic do innych chatów.

Worktree: C:/Users/Arek/.codex/worktrees/bolt-014-monthly-income-api/MyHomeBudget. Branch feat/bolt-016-periods-income-ui.

## Metoda i zakres

Odczyt źródeł, analiza sekwencji stanów/async oraz porównanie z implementation-plan.md, standardem kodu i rzeczywistymi backendowymi serializerami, views, services i exception codes. Autor zmieniał kod w trakcie przeglądu; uwagi przekazywano od razu, po czym recenzent ponownie odczytał poprawione fragmenty. Tabela hashów określa oceniony końcowy snapshot tego przeglądu.

Przejrzano lata/miesiące, IncomeList, IncomeForm, IncomeAttachments, PeriodsPanel, IncomeSourceCreate, wspólne api.ts i periods-api.ts, nowy income-response.ts, wydzielone OtherSourceForm/CompanyDialog, ContractForm/CompanyCreateForm/ActionForm i integrację HouseholdShell/Application. Sprawdzono style periods.css źródłowo oraz końcowe renderowane widoki z implementation-captures.

Kontrakty backendu: AccountingYearOutput/CreatedOutput, AccountingMonthOutput, IncomeCreateInput/PatchInput/DeleteInput, IncomeOutput/SourceOptionOutput/TotalsOutput, IncomeAttachmentOutput oraz source_option_data/_income_response/create_income_record. Deklaracje frontendowe po poprawce odpowiadają konsumowanym rzeczywistym polom; sumy pochodzą z API, kwoty nie są konwertowane do float. Contract bruto pobierany przez rzeczywisty endpoint contracts, nie fikcyjny element SourceOption.

Nie uruchamiałem tutaj testów, środowiska aplikacji, buildów ani quality. Nie podaję wyników autora jako niezależnego PASS. Odbiór renderu opiera się na samodzielnym obejrzeniu JPEG wykonanych przez rodzica z aplikacji; nie zastępuje interaktywnego audytu klawiatury, pełnej geometrii DOM ani E2E z rzeczywistym backendem.

## Ocena

| Kryterium przeglądu kodu                 | Ocena | Uzasadnienie                                                                                                                                                       |
| ---------------------------------------- | ----: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Zgodność domeny i API                    |   9,0 | Stan serwerowy, słownik źródeł, rzeczywiste dziesiętne kwoty, per-currency totals, prywatne attachments i poprawione SourceOption.                                 |
| Integralność zapisu i konflikty          |   8,5 | Idempotentna ręczna próba, zmienione pola PATCH/expected_version, preserved mergeScratch, walidacja envelope, kontrola uncertain upload. Wymaga testów brzegowych. |
| Role i kontekst async                    |   8,5 | canManage, odczyt aktywności, samodzielne rozstrzygnięcie membership/allSettled, abort na year/month i kontrola id.                                                |
| Zgodność przepływu i dostępność źródłowa |   8,0 | Shared forms, pending propagation, inline focus/Escape/restore i jawne błędy. Semantyka JSX nie dowodzi zachowania runtime.                                        |
| Utrzymanie i dowody                      |   7,5 | Logika API/form/presentation rozdzielona i reużywana; testy i runtime dopiero powstają. Nie przyznano za nie punktów jako za wykonane.                             |

Średnia równych wag = 8,3. To osobna ocena kodu; nie zastępuje ani nie aktualizuje ocen pięciu wizualizacji sidebar-v3 (8,40–8,50).

## Uwagi znalezione i zweryfikowane po poprawkach

1. **P2 — utrata szkicu przy ręcznym scalaniu — resolved.** IncomeForm wcześniej zastępował values danymi konfliktu i zerował conflict. Obecnie zapisuje niezależne mergeScratch z wartościami i nazwami przed zmianą baseline; zachowany szkic jest renderowany osobno. Scenariusz Test: szkic8200/30.03 vs serwer8100/31.03 → rozpoczęcie ręcznego scalania zachowuje oba konteksty i używa nowej wersji.

2. **P2 — edytowalny formularz po zmianie roli — resolved.** IncomeForm disabled uwzględnia canManage(context.household). Odświeżenie roli nie może pozostawić działającego finansowego formularza zapisu. Scenariusz: administrator→viewer w otwartym formularzu, odczyt nowej roli; pola/submit zablokowane. Backend nadal autorytatywny.

3. **P2 — pending quick-add/firmy niewidoczny dla guard — resolved.** ActionForm udostępnia onPendingChange; OtherSourceForm/ContractForm/CompanyCreateForm/CompanyDialog propagują je przez IncomeSourceCreate do sourcePending. Zablokowane zmiana rodzaju/anulowanie i nawigacja podczas POST. CompanyDialog blokuje cancel/Escape przy pending. Test: opóźniony POST źródła/umowy/firmy; próba przejścia do innego gospodarstwa/rodzaju/sekcji nie gubi trwającego zapisu.

4. **P2 — stale dane potwierdzenia DELETE/przejścia i niewidoczny błąd — resolved.** IncomeList/AccountingMonths zamykają nieaktualny ConfirmAction dla403/404/409, odświeżają dane/recheck, a actionError jest także wyświetlany poza panelem role=alert. Test: DELETE409 po innej edycji; close409 po innej zmianie stanu; nowa akcja z odczytanych danych, błąd nie znika z dialogiem.

5. **P2 — stary GET odblokowywał retry unknown upload — resolved źródłowo.** IncomeAttachments ma listGeneration; przejście unknown zwiększa generację i zeruje checked. GET listy rozpoczęty wcześniej nie może ustanowić nowego checked. Test: opóźnij stary GET, POST o nieznanym wyniku, zwróć starą listę; retry pozostaje zablokowany do nowego odczytu oraz jawnego potwierdzenia możliwości duplikacji.

6. **P2 — brak odzyskania members po błędzie GET — resolved.** IncomeForm ma prerequisiteRevision, a Odśwież źródła ponawia prerequisites i source options. Test:503 members przy zachowanej kwocie/dacie → retry bez reloadu i utraty szkicu, odzyskane osoby/źródła.

7. **P2 — membership odrzucone przez Promise.all i późny recheck innego okresu — resolved.** PeriodsPanel używa allSettled: utrata członkostwa403/404 lub brak household ustawia unavailable niezależnie od błędu months. Cleanup abortuje po zmianie year/month; apply sprawdza id miesiąca. Test: utrata członkostwa i late odpowiedź starego roku/miesiąca nie przywracają danych ani nie nadpisują nowego kontekstu.

8. **P2 — quick-add poza viewportem bez fokusu i pułapka Escape — resolved.** IncomeSourceCreate przenosi fokus/scroll do panelu, przywraca trigger, chroni szkic i zmiany rodzaju. Escape wrappera ma !dialog && !discard; nie odtwarza anulowanego potwierdzenia. Test klawiaturą: otwarcie, Escape przy dirty, Escape na potwierdzeniu → zostaje szkic, potwierdzenie znika raz, dalsze anulowanie przywraca trigger.

9. **P2 — niepoprawny201 JSON mógł zakończyć próbę jako404 — resolved.** confirmedIncome sprawdza identyfikatory i kontekst, version, wartości i konsumowane snapshoty przed użyciem saved.id i po aktualnym GET. Wadliwa odpowiedź daje ApiError0, a POST zachowuje unknown/klucz; nie tworzy endpointu /undefined/ i nie udaje potwierdzonego zapisu. Test:201{} / błędny household/month / brak snapshotu → unknown, bez uploadu, retry tym samym kluczem.

10. **P2 — unknown po definitywnym odrzuceniu pozostawał na zawsze — resolved.** Po ręcznym retry400 lub income_period_not_active formularz rozstrzyga unknown, zachowuje szkic i pozwala na poprawę albo jawne zarządzanie okresem. Nie rozstrzyga idempotency_conflict jako dowodu braku wpisu. Test: timeout bez commit→retry400 oraz timeout bez commit→zamknięcie→retry409; osobno klucz użyty do innego payloadu, który ma pozostać nierozstrzygnięty.

11. **P3 — fikcyjne gross pola SourceOption — resolved.** periods-api.ts contract ma obecnie company_id/company_name/contract_type/other_type_name zgodne z _contract_snapshot. gross_amount/gross_basis nie są deklarowane jako zwracane przez options API; widok brutto korzysta z Contract.

Wszystkie powyższe rozstrzygnięcia są ponownym przeglądem źródeł, nie deklaracją, że scenariusze Test wykonano.

## Końcowe poprawki i odbiór rzeczywistego renderu

Ponownie odczytano końcowe cztery miejsca zmian w commit 3c0d1b5:

- **IncomeForm lifetime zapisu — accepted.** Oddzielny AbortController powstaje przy montowaniu i kończy się przy odmontowaniu. Ponowny odczyt prerequisites nie abortuje POST/PATCH ani nie gubi wyniku zapisu. Po abort stan/callback nie są aktualizowane. Lock zwalniany w finally.
- **ConfirmAction danger — resolved P3.** Wspólny opcjonalny wariant primary/danger stosowany dla usuwania przychodu/załącznika i odrzucenia szkicu (także quick-add); przejścia miesiąca zachowują primary.
- **HouseholdShell logout — accepted.** Normalny logout jest awaitowany przez ActionForm. Po potwierdzeniu opuszczenia brudnego formularza async logout ma catch i widoczny navigationError, zamiast nieobsłużonego odrzucenia. Guard nadal blokuje busy/unknown.
- **PeriodsPanel allSettled — accepted.** Membership i stan okresu rozstrzygane niezależnie; utrata dostępu 401/403/404 albo brak gospodarstwa blokuje dane również przy błędzie drugiego żądania. Cleanup abortuje stary kontekst; aktualizacja miesiąca sprawdza oczekiwane id.

Nie stwierdzono nowych P1/P2 w tym ograniczonym końcowym przeglądzie. Wcześniejsze uwagi pozostają resolved źródłowo; nie deklarujemy niezależnego wykonania ich scenariuszy integracyjnych.

### Render: accepted dla każdego widoku

Recenzent samodzielnie obejrzał wszystkie **18 JPEG** w evidence/implementation-captures: years, months, income, summary, attachments, summary-empty; każdy przy 1440, 1024 i 390. Są to przechwycenia implementacji rodzica, a nie pierwotne makiety HTML. Nie przeprowadzono własnej sesji browser ani nie odtwarzano pobierania plików.

| Widok            | 1440 | 1024 | 390 | Decyzja i uzasadnienie                                                                                      |
| ---------------- | ---: | ---: | --: | ----------------------------------------------------------------------------------------------------------- |
| Lata             |  8,5 |  8,5 | 8,5 | accepted: obecny sidebar/topbar, jasny kontekst, osobne CTA, jedna kolumna na mobile.                       |
| Miesiące         |  8,5 |  8,5 | 8,5 | accepted: 12 kart w kolejności, równe karty, 3/2/1 kolumny, odrębne wejście i zmiana stanu.                 |
| Formularz        |  8,5 |  8,5 | 8,5 | accepted: równe pola, dwa/jeden słupek, słownik źródeł, kwota i data, czytelny focus; brak paska prototypu. |
| Lista i sumy     |  8,4 |  8,4 | 8,4 | accepted: waluty oddzielne, historyczny opis, akcje; na mobile lokalnie przewijana tabela zgodna z planem.  |
| Załączniki       |  8,5 |  8,5 | 8,5 | accepted: kontekst wpisu, osobna lista i dodawanie, czytelne limity, jedna kolumna na mobile.               |
| Pusta lista/sumy |  8,5 |  8,5 | 8,5 | accepted: jawny brak przychodów, brak fikcyjnych zer, zachowane CTA i kontekst.                             |

Każdy wynik jest ściśle >7,5. Mobile sidebar układa się nad treścią zgodnie z obecnym shellem; brak globalnego paska Lata/Miesiące/Formularz/Podsumowanie/Załączniki. Nawigacja kontekstowa Lata / Rok / Miesiąc widoczna jako breadcrumbs. Widoczny obrys pola daty jest stanem focus, nie wadliwą obramówką. Na JPEG nie widać rozsuniętych pól ani uciętych paneli; mobilna tabela celowo wykracza w swoim lokalnym regionie przewijania. JPEG nie dowodzi pomiaru scrollWidth ani pełnej dostępności.

### Wyniki walidacji przekazane przez rodzica

Rodzic potwierdził końcowy build oraz scripts/quality.ps1 exit 0. Pełny Playwright: **67 passed, 8 skipped (75 przypadków)**; wszystkie **24 nowe testy PASS**. Recenzent odczytał test periods-income.spec.ts i potwierdził korzystanie z mockPeriods: testy UI z odpowiedziami API zastąpionymi fixtures nie stanowią E2E PASS rzeczywistego backendu. Wyników tych nie uruchamiano niezależnie w tej sesji. Pominięte testy nie są PASS. Formalny etap Test i bolt 017 nie są zamykane tym raportem.

## Wymagane przed końcowym Test/boltem

- Niezależny render pięciu ekranów przy1440/1024/390 accepted powyżej. Nadal należy domknąć rzeczywisty Compose /api, DOM overflow, klawiaturę, długi basename/kwotę graniczną i role.
- Role matrix i 12 inactive po utworzeniu roku, wiele aktywnych/dowolna kolejność, close/reopen, read-only załączniki.
- Osoba/gospodarstwo, quick-add innego źródła/umowy/firmy i brak automatycznego brutto/przychodu; historyczne nazwy/powiązania.
- Paginacja powyżej50, sumy całego okresu i kilku walut, niezależne błędy sum.
- Wszystkie scenariusze napraw1–10, w szczególności malformed201, unknown400/409, retained conflict draft, stale upload GET i context.
- Upload201 poprawnych metadata, limity/typy, brak automatycznego retry uploadu, partial income+files, authenticated download/delete.
- Build/quality i testy UI rodzica potwierdzone jako przekazane wyniki powyżej; wymagane rzeczywiste E2E i brakujące przypadki pozostają otwarte.
- Kolejne większe zmiany wymagają nowego scoped review. Ocena dotyczy hashowanego snapshotu i nie zamyka Test.

## SHA256 snapshotu

| Plik                                             | SHA256                                                           |
| ------------------------------------------------ | ---------------------------------------------------------------- |
| frontend/app/lib/api.ts                          | 833BFDCA639677AEBBBF85554DA94B1595721DD235D3A76679A905FBDEB979E3 |
| frontend/app/lib/periods-api.ts                  | BF9B677D6B3660BFEDFB0AE8F569247E239E93A0106C7C122618C30881D0E59E |
| frontend/app/lib/income-response.ts              | 9AB02BC53A207834F4E31B15DD14ACF287C7C5F9BB839240C6742326406EDD90 |
| frontend/app/components/income-form.tsx          | 9FB22920244EE98C65DE9223099EB48D693C52B536DEB67092BBE7ED98E33C0D |
| frontend/app/components/income-attachments.tsx   | 7171ED81C52534E33F387C1F8DA600B1D7A2DDA6AB5E4108AC512E61FA102D0F |
| frontend/app/components/income-list.tsx          | FAD92F68F2C8CF3626AAC06424F5D67665D938C8BA6A3406DBA0A024E1E0B72E |
| frontend/app/components/periods-panel.tsx        | 25A7FCB0EBFCB679C2E7A28B505105C64E271041803FA8D3C947A2E068DE686E |
| frontend/app/components/income-source-create.tsx | 9E4EE483C25E5968B912B26E641A99AE5798E8021CB8EA37E0025A12F6BDC05A |
| frontend/app/components/accounting-years.tsx     | E6DDC3C5E846BB4339C55AC22DD6DA6EBA4AA6B9002843B497CABF9CE5C26E41 |
| frontend/app/components/accounting-months.tsx    | D7D9A299642548A9D8FFAABFEE8D3BDCB09D50DE2B90223B8BD431701BE29CBC |
| frontend/app/components/periods-common.tsx       | 7B37671E25D39AD507586CB4FE579846233263BEFDD74531E6F80A52581DBE11 |
| frontend/app/components/other-source-form.tsx    | 58E57D7B04406250232F005581C6CD1BC42DDD6CD3D5B49F5E5D7CAC58CEE60A |
| frontend/app/components/contract-form.tsx        | 1C44AB77D9351B01D54E3CE2DEBC16636FC75C52A97BE6DD04E85D8C2B75189C |
| frontend/app/components/company-dialog.tsx       | 03B9101A468FDA91C81E3EB177E074916A762FBEFED37A4ACA945DC1923EBFE9 |
| frontend/app/components/company-panel.tsx        | BE810AC3BB9D53A8ECDFC67CAEBC6455329CC29558DDED569B44EAF5E39779BC |
| frontend/app/components/ui.tsx                   | 1A7F90A205E8594C235088CE0FDBFF82104496E9B4B9081C7EB0BF44A6716129 |
| frontend/app/components/household-shell.tsx      | E58E6F5AC1AA154AABDD916B4AE487E04155B39AFB1DBCEBD8C3CF0F374B20C7 |
| frontend/app/components/application.tsx          | A8300C891DEFC4B2AD44989C2A2FDB8419BA8FCBEF6C6187185AEEAD805429A9 |
| frontend/app/periods.css                         | FD500E3FDA10A800217CD6583FFB4545356A549FB7CEC67C9A1170BAE2096D38 |

## SHA256 dowodów renderu

| Plik                                           | SHA256                                                           |
| ---------------------------------------------- | ---------------------------------------------------------------- |
| implementation-captures/attachments-1024.jpg   | 7E12B66469FF63C0D738CB446109B68F9ED8E585874A255FB1DB6A9233BA694D |
| implementation-captures/attachments-1440.jpg   | 2447289962629D7E159F182975D6B1A3E251A4CF65652A63720E3E5A992E98FB |
| implementation-captures/attachments-390.jpg    | BB10AA9837FCE499EA7E47A350609BD6EBA8E5C2B27E6663100CA73FC0DDEF92 |
| implementation-captures/income-1024.jpg        | 850E50AC982616EE88CB3FC92BFE899482551C8458802DDBA5D31A6531117CEF |
| implementation-captures/income-1440.jpg        | CDE084B86731E4E5BB884FB770287422E476FB6C0F94BDD592B827BEA8AF0D46 |
| implementation-captures/income-390.jpg         | 70CDE41326EBF567B4B2E423A2C10B88DDD5EFDA7859C63054C56D1B272EC0A6 |
| implementation-captures/months-1024.jpg        | 693FDFF60C8977DAC8B221E72E21D52F0B38EC325675314A46FE076B0F88D821 |
| implementation-captures/months-1440.jpg        | BE284F63C0CD77C93B761FB9ED8E2EE02529A5B5889DF5BECAD89B92C599C79E |
| implementation-captures/months-390.jpg         | FE2542BB290536B6DB0416B51CEB224BFE52F1B3D9910F8D2976082FACC04CBE |
| implementation-captures/summary-1024.jpg       | 9B4C6F7B0145C1E59BC8BCA390583BC1E7E83C980653CD6CFE7D4BE0B60163DF |
| implementation-captures/summary-1440.jpg       | 54AE5CC6799AAE650EE8773C33108C12213D9E49B9B95178AC590BA4F8349EF0 |
| implementation-captures/summary-390.jpg        | 08D56B7EF6DC819C8FA3C17B88F0BB3BDC71A57EE7BA0871BFCD88E054ED9D66 |
| implementation-captures/summary-empty-1024.jpg | A9DBF7EA3DB5CD88C7495DFB6CBE765DE7DE6800FF3DE72AF6D1CB15BD070AB8 |
| implementation-captures/summary-empty-1440.jpg | 0EACDFE7B5FAA287AB60FD031DA85FF6BF96097A9CBFFAF568B3BC31F36CDDFD |
| implementation-captures/summary-empty-390.jpg  | 6653D542BBFE506A1BB3DF9A4F103078D52246BF29E0B3209A47B9BF800DD9D6 |
| implementation-captures/years-1024.jpg         | 1F7C485DB824D2C9FFB64F20128EEBE36AEC62DF60653FAE5F6B19BABB876AFD |
| implementation-captures/years-1440.jpg         | CAEA0ABBABA8694EA7476B8A317587AE2B35A04041896634F77C2299F3EE4592 |
| implementation-captures/years-390.jpg          | 4185291E6940AAF1C19BAC3AE0D5732A3F18EEBE5CF3ABBAE54B27B4A0A5081E |
