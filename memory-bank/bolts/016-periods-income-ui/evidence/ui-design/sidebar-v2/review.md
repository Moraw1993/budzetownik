---
artifact: independent-ui-review
version: sidebar-v2
reviewer: /root/review_ui016
reviewed_at: "2026-10-09T07:52:26+02:00"
decision: changes-required
scope: isolated-plan-and-visualizations-only
---

# Niezależny przegląd UI bolta 016

Recenzent: osobny subagent /root/review_ui016; nie jest autorem planu ani prototypów. Oceniono plan oraz rzeczywisty render HTML/CSS. **Decyzja całego checkpointu: changes-required**. Lata, miesiące, lista/podsumowania i załączniki mają zaakceptowany kierunek. Przed akceptacją całości trzeba domknąć dwa stany formularza przychodu wskazane poniżej. Wynik liczbowy ponad 7,5 nie usuwa blokujących braków przepływu.

## Zakres i dowody

Worktree: C:/Users/Arek/.codex/worktrees/bolt-014-monthly-income-api/MyHomeBudget. Branch feat/bolt-016-periods-income-ui; baza origin/develop 29fc7e3.

Źródła: implementation-plan.md, bolt.md, wszystkie pięć stories UI, memory-bank/standards/ui-design-review.md i design-system.md; pomocniczo istniejący OtherSourceForm, IncomeCreateInput/IncomePatchInput i pola odpowiedzi API.

Rzeczywiście otwarto własną kartę cua_repl pod http://127.0.0.1:8097/ i obejrzano screenshoty:

- Desktop 1440x1000: pięć ekranów, Y-add, M-close/M-activate/M-reopen, I-source, I-contract/I-company, S-delete, A-delete oraz A-unknown/A-readonly/A-download.
- Mobile 390x844: pięć ekranów, Y-add/pusty/błąd, wszystkie trzy M-confirm, M-readonly/konflikt, I-source/I-contract, I-error/I-conflict, S-delete/pusty/ładowanie/błąd, A-delete/pusty/ładowanie/błąd oraz A-unknown/A-readonly/A-download.
- DOM/AX obejmuje pozostałe stany. Wąskie długie formularze przewijają się pionowo; widoczna część i geometria pól została oceniona. Nie twierdzę, że każda część każdego długiego formularza była jednocześnie widoczna na screenshotach.
- Odczyt geometrii na 390px: documentElement.scrollWidth=375 dla każdego z pięciu widoków, innerWidth=390. Brak poziomego overflow strony dla pokazanych danych.
- Tabela przychodów: region 301px, scrollWidth=740, tabindex=0 i podpis aria-label. ArrowRight rzeczywiście zmienił scrollLeft z 0 do 8; screenshot pokazuje lokalny pasek przewijania i zielony fokus. Fokus Pobierz w załącznikach też widoczny.
- Override viewport przywrócono przez reset().

Pasek „Podglądy ekranów”, ostrzeżenie o prototypie i sekcja kolejnych wariantów służą przeglądowi. **Nie są propozycją produkcyjnej nawigacji**. Sidebar zostaje zgodnie z korektą użytkownika; PNG z 8 października nie są zatwierdzonym projektem.

Prototyp jest celowo statyczny. Nie odrzucam go za brak wywołań API, zapisu, logiki ról czy fokusowania inline paneli. Statyczne hashe nie dowodzą działania produkcyjnych interakcji. Oceniona dostępność dotyczy etykiet, semantyki widocznych pól/statusów, kontrastu wzorca, rozmiarów i dwóch powyższych kontroli klawiatury; to nie jest pełny audyt WCAG. Nie testowano screen readera, wszystkich treści skrajnych, 1024px ani HTTP aplikacji.

## Oceny pięciu widoków

Pięć równych wag; Score=(U+H+D+A+R)/5, próg przed zaokrągleniem. U=użyteczność/wymagania; H=hierarchia/czytelność; D=design system; A=dostępność; R=responsywność/stany.

| Widok                             |   U |   H |   D |   A |   R | Score | Decyzja          |
| --------------------------------- | --: | --: | --: | --: | --: | ----: | ---------------- |
| Lata — years.html                 | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted         |
| Miesiące — months.html            | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted         |
| Formularz przychodu — income.html | 7,5 | 8,5 | 8,5 | 8,0 | 6,5 |  7,80 | changes-required |
| Lista/podsumowanie — summary.html | 9,0 | 8,5 | 8,5 | 8,0 | 8,0 |  8,40 | accepted         |
| Załączniki — attachments.html     | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted         |

Uzasadnienia:

- Lata: prosty wybór; brak wymyślonych statusów/sum roku; świadome utworzenie 12 inactive. Czytelne karty, jasne tło i zielone akcje. Widoczne etykiety i komunikaty. Mobile jedna kolumna; pusty, duplikat, ładowanie i błąd pokazane.
- Miesiące: 12 po kolei, wiele active, jawne przejścia i dozwolony odczyt inactive/closed. Nazwa miesiąca i tekst badge mają dobrą hierarchię. Zachowany shell. Potwierdzenia mają jawne skutki i Anuluj. Jedna kolumna na telefonie; role/konflikt pokazane bez sugerowania edycji czy ukrytej aktywacji.
- Formularz: osoba/gospodarstwo i źródło słownikowe; oddzielenie brutto od rzeczywistej kwoty, daty poza okresem i osobny zapis plików są zgodne. Układ pól jest równy, quick-add nie rozciąga sąsiedniego pola. Label i błąd kwoty są czytelne; rozmiary podstawowych pól/akcji właściwe. R obniżają dwa niedomknięte stany nieznanego zapisu i konfliktu — ich brak dotyczy projektu przepływu, nie braku implementacji JS.
- Podsumowanie: zgodne sumy per waluta i historyczne nazwy; pięć wpisów daje dokładnie 12 000 PLN. Oddzielne grupy miesiąc/rok bez kursów. Czytelna tabela i dostępne akcje. Lokalny podpisany scroll potwierdzony klawiaturą. Na telefonie kwota/akcje wymagają przewinięcia tabeli, ale są dostępne; nie ma overflow całej strony.
- Załączniki: kontekst przychodu, prywatny download, zapisane vs oczekujące, limity MiB i nieznany upload są poprawnie rozdzielone. Dobra hierarchia dokumentów i zajętości. Akcje z tekstem, widoczny fokus. Mobile zawija akcje bez obcięcia. Brak pozornej gwarancji rollbacku i automatycznego retry.

## Pomocnicze panele — ocena osobna

| Panel                                         |   U |   H |   D |   A |   R | Score | Decyzja              |
| --------------------------------------------- | --: | --: | --: | --: | --: | ----: | -------------------- |
| Y-add                                         | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| M-confirm — aktywacja                         | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| M-confirm — zamknięcie                        | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| M-confirm — ponowne otwarcie                  | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| I-source                                      | 8,5 | 8,5 | 8,5 | 8,0 | 8,0 |  8,30 | accepted             |
| I-contract                                    | 8,5 | 8,5 | 8,5 | 8,0 | 8,0 |  8,30 | accepted             |
| I-company — istniejący wzorzec wewnątrz umowy | 8,5 | 8,5 | 8,5 | 8,0 | 8,0 |  8,30 | accepted-layout-only |
| S-delete                                      | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| A-delete                                      | 8,5 | 8,5 | 8,5 | 8,0 | 8,5 |  8,40 | accepted             |

Panele używają tego samego shellu/powierzchni, nagłówków, tekstowych skutków, labeled pól i konkretnych CTA z Anuluj. Quick-add zachowuje oddzielenie źródła od faktycznego wpływu; plan wskazuje reużycie pełnych istniejących formularzy (frequency enum w prototypie jest skróconą próbką, nie specyfikacją redukcji opcji). I-company to pokazany istniejący wzorzec — makieta karty nie zatwierdza zamiany istniejącego modalu ani jego semantyki. Ich oceniony układ jest poprawny; wspólne błędy pól należy wdrożyć jak planuje autor.

## Numerowane uwagi

1. **[P2, blokada formularza] Brak wizualizacji nieznanego wyniku POST przychodu.** Plik income.html, sekcja wariantów po I-error; implementation-plan.md linia 81. Plan trafnie wymaga tego samego Idempotency-Key i payloadu, lecz użytkownik widzi tylko błąd walidacji, sukces albo partial sukces plików. Nie pokazano komunikatu „przychód mógł być zapisany”, bezpiecznej ręcznej akcji sprawdzenia tej samej próby ani sposobu zahamowania edycji payloadu przed rozstrzygnięciem. Poprawka: odrębny I-unknown z konkretnym CTA, zachowanymi danymi i opisem dalszego wyniku. Doprecyzować w planie, że sprawdzenie może być idempotentnym ponowieniem POST z identycznym body/kluczem; sama lista oraz podobna kwota/nazwa nie dowodzą tożsamości zapisu. Pokaż obsługę ponownej utraty odpowiedzi bez nowego klucza. Nie trzeba implementować API w prototypie.

2. **[P2, blokada formularza] Konflikt edycji nie przedstawia porównania zachowanego szkicu z aktualnym zapisem.** income.html:297–329; implementation-plan.md:81. I-conflict mówi „porównaj”, ale prowadzi do I-edit zawierającego jeden zestaw pól. Nie wiadomo, która wartość jest szkicem, która serwerową, ani co stanie się po kliknięciu „Zapisz zmiany”. Poprawka: wizualny wariant I-compare z oznaczeniem „Twój szkic”/„Aktualnie zapisane”, wyborem powrotu do szkicu/rezygnacji oraz jawnym zatwierdzeniem ponowienia na odczytanej wersji; zachować lokalne wartości bez cichego nadpisania. Przy tym doprecyzować zwykłą edycję odbiorcy i źródła: API IncomePatchInput dopuszcza member_id/source_id, a obecny I-edit pokazuje tylko stały tekst historyczny. Pokazać możliwość świadomej poprawy tych powiązań albo wyraźnie uzasadnić ograniczenie do kwoty/waluty/daty w zaakceptowanym zakresie. Niezmienione historyczne powiązania mają pozostać bez ponownej walidacji; zmienione muszą używać słownika dostępnego dla nowego odbiorcy/okresu.

3. **[P3, do poprawy przy domknięciu] A-delete kieruje w prototypie do komunikatu „Pliki zapisane / Dodano pliki”.** attachments.html: A-delete i A-success. To wspólny statyczny link, więc nie traktuję go jako błędu produktu, lecz copy nie pokazuje poprawnego zakończenia usunięcia. Warto dodać A-delete-success: „Załącznik usunięty” i odświeżona lista.

4. **[P3, wymaganie testu implementacji] Długie niełamliwe nazwy plików i duże kwoty.** preview.css .file-row/.amount i attachments.html/summary.html. Pokazane dane nie overflowują. CSS nie zawiera jawnej reguły łamania długiego basename; to ryzyko wywnioskowane ze źródła, nie zreprodukowany render. W implementacji dodać przypadek nazwy bez spacji i kwoty granicznej na 390px, overflow-wrap/min-width tam gdzie potrzebne. Nie obcinaj jedynej identyfikacji dokumentu bez dostępnej pełnej nazwy.

## Wersja ocenionych plików — SHA256

| Plik                   | SHA256                                                           |
| ---------------------- | ---------------------------------------------------------------- |
| implementation-plan.md | 672EC1F9DA0DFEAEA261DF731212F2C6AD2DA814B9DC9E4A676F19872460D62F |
| years.html             | 3F5113C5E00F76ABB79D096D8B2A1422BE989569754502E0C9D57666EF3BA279 |
| months.html            | CE1C9FFF26C75C86ACE7720B98D98C7984D5D617F07AD0EBFC608B2ED095BE47 |
| income.html            | 5235B36A03B68D420355B3ADC1B147936758057E67837363EE83D3A18841278E |
| summary.html           | DD05C2065A903977EB944524453CA28CF4832CECF1581CF92EE58A668D051382 |
| attachments.html       | 80434ECB125E926AB6F312B731E22157F4C1797FF6880C4CF5FD8F26DF9F079E |
| preview.css            | 1AC091F3DF7969E54B5F188CA60B90EC554E0C469F601FC3206FF8BD166AFFAB |

## Następny checkpoint

Poprawki 1 i 2 wymagają aktualizacji planu i odizolowanej wizualizacji, a następnie ponownej niezależnej oceny tych stanów i ich desktop/mobile. Po accepted bez blokad i każdym Score >7,5 konieczna jest jawna zgoda użytkownika na konkretną ocenioną wersję zgodnie z bramką. Nie rozpoczęto implementacji produkcyjnej w ramach tej recenzji i nie wysłano nic do innych chatów.
