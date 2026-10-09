---
artifact: independent-ui-review
version: sidebar-v3
reviewer: /root/review_ui016
reviewed_at: "2026-10-09T08:03:11+02:00"
decision: accepted
scope: isolated-plan-and-visualizations-only
user_acceptance: pending
---

# Niezależny przegląd UI bolta 016 — sidebar-v3

**accepted**: wszystkie pięć widoków oraz oceniane pomocnicze panele mają Score >7,5/10; brak blokujących problemów projektu. Dwie blokady formularza z raportu sidebar-v2 są rozwiązane. Sidebar pozostaje zgodnie z decyzją użytkownika. Ta niezależna akceptacja projektu **nie jest zgodą użytkownika na implementację** i nie potwierdza działania API/frontendu.

Recenzent: osobny subagent /root/review_ui016, niebędący autorem planu, prototypów ani nowych screenshotów. Ocena dotyczy wersji źródeł opisanej hashami poniżej, a nie wcześniejszych kanw PNG.

## Dowody i sposób oceny

Worktree: C:/Users/Arek/.codex/worktrees/bolt-014-monthly-income-api/MyHomeBudget. Branch feat/bolt-016-periods-income-ui; baza origin/develop 29fc7e3. Plan: memory-bank/bolts/016-periods-income-ui/implementation-plan.md. Wizualizacje: evidence/ui-design/sidebar-v3/{years,months,income,summary,attachments}.html oraz preview.css.

Przeczytano plan v3, poprzedni raport i wszystkie zmienione stany; zachowano kontekst standardów ui-design-review.md, design-system.md, bolta i pięciu stories z pierwszej oceny. Sprawdzono backend IncomePatchInput oraz create_income_record: identyczna próba z utrwalonym kluczem odczytuje wcześniejszy envelope przed require_active_month. Nie istnieje GET po kluczu — plan v3 poprawnie stosuje ręczne idempotentne ponowienie POST i późniejszy odczyt bieżącego wpisu.

**Ograniczenie narzędzia recenzenta:** po pierwszej ocenie moja sesja cua_repl zgłaszała niedostępność browser id2/iab; inventory zwróciło apps:[] i browsers:[]. W v3 nie wykonałem własnej sesji interakcyjnej. Root przechwycił realny render udokumentowanym CUA; ja samodzielnie obejrzałem przez view_image **wszystkie 27 obrazów** z captures/ i porównałem je z planem/źródłami. Nie przyjąłem oceny autora jako dowodu.

Autor screenshotów: /root. Ścieżka: evidence/ui-design/sidebar-v3/captures/. Obejrzano:

- years-1440/390.jpg, months-1440/390.jpg, income-1440/390.jpg, summary-1440/390.jpg, attachments-1440/390.jpg — wszystkie pięć ekranów desktop i mobile;
- I-unknown, I-checking, I-recovered, I-conflict, I-merge, I-edit, I-unsaved-changes — każdy w wariancie 1440 i 390;
- A-long-390.jpg, A-removed-390.jpg i S-boundary-390.jpg.

captures/metrics.json rejestruje rzeczywiste document.clientWidth oraz scrollWidth: 1440/1440 dla pięciu desktopów, 390/390 dla pięciu telefonów i trzech przypadków skrajnych. Autor skorygował viewport override dla zoomu IAB (requested1599 dla CSS1440, requested444 dla CSS390). Są to pomiary autora, niezależnie od mojego oglądania screenshotów; obrazy są z nimi zgodne. Nie twierdzę, że wykonałem te pomiary w swojej sesji. Autor poinformował o reset() viewport po przechwyceniu; ja swój override zresetowałem po v2.

Panele Y-add/M-confirm/I-source/I-contract/I-company/S-delete/A-delete zachowują oceniony wcześniej układ. W v2 recenzent sam oglądał je przez cua_repl desktop/mobile; w v3 ich strukturę porównano ze źródłami i powiązano z tym samym CSS, z ograniczonymi poprawkami (tekst sidebaru, checkbox, zawijanie kwot/nazw). Obrazy v3 pokrywają nowe lub istotnie zmienione stany; nie twierdzę, że v3 posiada osobny nowy screenshot każdego niezmienionego pomocniczego panelu.

„Podglądy ekranów”, żółta informacja prototypu i stos wariantów są wyłącznie narzędziem przeglądu — **nie są produkcyjną nawigacją**. Screenshoty obejmują rzeczywisty render odizolowanego statycznego HTML, nie wdrożony ekran aplikacji.

## Ograniczenia

Prototyp nie dowodzi HTTP, działania ról, zapisu, timingu, przechodzenia fokusu, Escape ani ochrony szkicu. Niewywołanie API w makiecie nie jest wadą projektu. W v2 sprawdzono dwie podstawowe akcje klawiatury (lokalny scroll tabeli i fokus Pobierz), ale v3 nie ma nowego testu interakcyjnego recenzenta. Nie testowano screen readera, pełnego WCAG ani viewport1024. To obowiązki późniejszego odbioru produkcyjnego frontendu.

Font wizualizacji jest systemowym fallbackiem przy deklaracji Geist, ponieważ statyczny prototyp nie ładuje lokalnego @fontsource-variable/geist. Produkcja ma użyć istniejącego Geist z design systemu; odbiór implementacji musi sprawdzić geometrię i zawijanie po rzeczywistym fontcie. JPEG i zoom przeglądarki ograniczają ocenę dokładnej ostrości/rozmiaru pikselowego. Nie utożsamiam obrazu z audytem wszystkich stanów runtime.

## Oceny pięciu widoków

Każde kryterium waży 20%; Score=(U+H+D+A+R)/5, próg sprawdzono przed zaokrągleniem. U=użyteczność/wymagania; H=hierarchia/czytelność; D=design system; A=dostępność projektu; R=responsywność/stany.

| Widok                             |   U |   H |   D |   A |   R | Score | Decyzja  |
| --------------------------------- | --: | --: | --: | --: | --: | ----: | -------- |
| Lata — years.html                 | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted |
| Miesiące — months.html            | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted |
| Formularz przychodu — income.html | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted |
| Lista/podsumowanie — summary.html | 9,0 | 8,5 | 8,5 | 8,0 | 8,0 |  8,40 | accepted |
| Załączniki — attachments.html     | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted |

Uzasadnienie pięciu kryteriów dla każdego widoku:

- **Lata:** U — prosty wybór i świadome utworzenie 12 inactive, bez wymyślonych stanów/sum roku. H — jasny nagłówek i karty z jednym działaniem. D — jasna treść, białe karty i zielona akcja, obecny sidebar. A — nazwane pola/działania i tekstowe komunikaty. R — jedna kolumna na telefonie, preserved context, pusty/duplikat/błąd/ładowanie opisane i ocenione w v2, bez regresji źródeł.
- **Miesiące:** U — 12 miesięcy po kolei, jawne activate/close/reopen, wiele active i odczyt inactive/closed. H — nazwa, badge i konkretne działania. D — zgodny shell i powierzchnie. A — stan tekstowy i wyjaśnienie skutków potwierdzeń. R — czytelne karty/akcje w jednej kolumnie, role i konflikt uwzględnione; nawigacja nie aktywuje miesiąca.
- **Formularz:** U — słownikowe źródło, osoba/gospodarstwo, rzeczywista kwota i data poza okresem; rozwiązane unknown/retry oraz konflikt/edycja powiązań. H — równe pola i dwa oznaczone zestawy szkic/aktualne. D — ten sam shell i formularze bez alternatywnej palety. A — etykiety, tekst błędu i konkretne CTA; dostępność wykonania pozostaje do testu produkcyjnego. R — nowe stany rzeczywiście czytelne mobile/desktop, kwoty i daty porównywalne, akcje zawijane, brak obcięcia.
- **Podsumowanie:** U — historyczne nazwy i wszystkie waluty osobno; pięć przykładów daje 12 000 PLN. H — oddzielne grupy miesiąc/rok oraz tabela. D — zgodne karty i działania. A — podpisany focusowalny region tabeli, tekstowe akcje i stany. R — lokalne przewijanie, nie cała strona; duża kwota pokazuje pełne cyfry na telefonie. Obniżenie względem innych wynika z konieczności przewijania tabeli do kwot/akcji na wąskim ekranie, co jest akceptowalne w tym wzorcu.
- **Załączniki:** U — kontekst wpisu, prywatny download, kolejka oddzielona od zapisanych, MiB i nieznany upload. H — dokumenty i ich stan identyfikowane tekstowo; osobny sukces usunięcia. D — zgodne powierzchnie i zielone/czerwone działania. A — labeled input, tekstowe Pobierz/Usuń oraz informacje o rolach. R — długi basename zawija się z zachowaniem pełnej nazwy, akcje pozostają dostępne; upload nie udaje procentowego postępu ani rollbacku.

## Pomocnicze panele — oceny osobne

| Panel                                    |   U |   H |   D |   A |   R | Score | Decyzja              |
| ---------------------------------------- | --: | --: | --: | --: | --: | ----: | -------------------- |
| Y-add                                    | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| M-confirm — activate                     | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| M-confirm — close                        | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| M-confirm — reopen                       | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| I-source                                 | 8,5 | 8,5 | 8,5 | 8,0 | 8,0 |  8,30 | accepted             |
| I-contract                               | 8,5 | 8,5 | 8,5 | 8,0 | 8,0 |  8,30 | accepted             |
| I-company — reużycie istniejącego wzorca | 8,5 | 8,5 | 8,5 | 8,0 | 8,0 |  8,30 | accepted-layout-only |
| I-edit                                   | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| I-conflict — porównanie                  | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| I-merge — ręczna korekta                 | 8,5 | 8,0 | 8,5 | 8,0 | 8,5 |  8,30 | accepted             |
| I-unknown                                | 9,0 | 8,5 | 8,5 | 8,0 | 9,0 |  8,60 | accepted             |
| I-checking                               | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| I-recovered                              | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| I-unsaved-changes                        | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| S-delete                                 | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| A-delete                                 | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |
| A-removed                                | 9,0 | 8,5 | 8,5 | 8,0 | 8,5 |  8,50 | accepted             |

Panele wspólnie zachowują zgodny wygląd, czytelną hierarchię i etykiety. Y-add i M-confirm wyjaśniają skutki oraz mają Anuluj. I-source/contract mają komplet podstawowych pól i plan reużycia istniejących formularzy — skrócony enum częstotliwości w prototypie nie redukuje istniejących opcji. I-company zatwierdza układ istniejącego wzorca; nie zatwierdza zastąpienia istniejącego modalu kartą ani pominięcia focus trap.

I-edit pokazuje powiązania historyczne i zasady ich świadomej zmiany. I-conflict odróżnia szkic8 200/30.03 od aktualnego8 100/31.03, a I-merge jawnie zaczyna na danych aktualnych, pokazuje szkic powyżej i pozwala anulować bez utraty. Na telefonie porównanie jest pionowe, czytelnie podpisane. I-unknown identyfikuje poprzednią próbę i wyjaśnia blokadę jej edycji/pliku; I-checking ma status zajętości; I-recovered osobno potwierdza wynik. I-unsaved ma bezpieczne Zostań oraz jawne Porzuć. S/A-delete identyfikują obiekt i skutek. A-removed ma poprawne copy usunięcia.

## Zamknięcie uwag v2

1. **P2 nieznany wynik POST — resolved.** Plan i widoki I-unknown/checking/recovered pokazują ręczne sprawdzenie tej samej próby, ten sam payload/klucz w implementacji, blokadę danych i plików do potwierdzenia oraz brak utożsamiania podobnych wpisów z sukcesem.
2. **P2 porównanie konfliktu i edycja powiązań — resolved.** Dwa jawnie oznaczone zestawy, ręczny merge na aktualnej wersji, kolejne konflikty ponownie do porównania oraz I-edit z odbiorcą/źródłem.
3. **P3 sukces usunięcia pliku — resolved.** A-delete odsyła do A-removed; „Załącznik usunięty / Usunięto potwierdzenie.pdf”.
4. **P3 długi basename/kwota — resolved for visualization.** A-long i S-boundary rzeczywiście widoczne mobile, pełne dane, brak obcięcia w obrębie karty; CSS ma overflow-wrap i min-width dla wiersza. Test rzeczywistego UI z Geist nadal konieczny.

## Drobne uwagi nieblokujące / odbiór implementacji

1. **P3 dokumentacyjny — resolved:** nagłówek tabeli planu poprawiono z „Wizualizacja v2” na „Wizualizacja v3”. Recenzent odczytał końcowy nagłówek i zweryfikował hash planu po formatowaniu oraz ustawieniu statusu awaiting-checkpoint. Nie zmieniło to projektu ani decyzji.
2. Po implementacji przetestować ręczny replay po kolejnej utracie odpowiedzi i po zmianie stanu okresu; przed uploadem odczytać aktualny wpis. Nie mylić odtworzonej dawnej odpowiedzi z aktualną dostępnością usuniętego wpisu.
3. Rzeczywiste zachowanie unknown próby przy nawigacji musi zachować możliwość sprawdzenia tego samego klucza/payloadu w bieżącej sesji; samo obejrzenie listy nie rozstrzyga próby. To konsekwencja zaakceptowanej reguły planu, nie nowy UI.
4. Produkcyjny odbiór ma obejmować pełne słowniki/paginację, historyczne powiązania, read-only, aktywny/closed/inactive, keyboard/focus/escape, role/status/error oraz lokalny scroll z Geist w1440/1024/390. Bez tego ocena makiety nie jest PASS implementacji.

## SHA256 ocenionych źródeł

| Plik                   | SHA256                                                           |
| ---------------------- | ---------------------------------------------------------------- |
| implementation-plan.md | 2CB0BDC3A4DD2E3137E60757170C51409495A71B3CC26CF93D652B44F9907E1F |
| years.html             | 0C9DC47FB90E17182BD86D369471313BEC25F1E392ACD19724254AF98F02FD4B |
| months.html            | E6D543639DF9393081F6BEEF36860FB086D3AA3CB7563B8034C0EFC791D1F70F |
| income.html            | EDEF872050B50E9F48BB7996944988140DF349179011490A6D0EFE496B52267B |
| summary.html           | BA96460C7CE84F84316E1C6B231153658A82D19558FB84FF7EE1D94DCAA9B0AB |
| attachments.html       | 65F17CDF518F36FF86A6A8BD2D972226480CFB57710E259BCF659A2B0E8AFE08 |
| preview.css            | 5FE4C47D485279A3DF3A371AA4F7ABBA0E0A3EF5E30D3111479E328690A18BEB |

Wskazane późniejsze korekty wyłącznie metadanych statusu/ścieżki raportu/nagłówka wersji planu nie zmieniają układu ani interakcji. Merytoryczne zmiany wymagają odpowiedniej ponownej oceny.

## Następny checkpoint

Niezależna ocena v3 zakończona accepted. **Jawna zgoda użytkownika na wdrożenie sidebar-v3 nadal oczekuje**, zgodnie z memory-bank/standards/ui-design-review.md. W ramach recenzji nie edytowano planu/prototypów/produkcyjnego kodu, nie commitowano i nie wysyłano wiadomości do innych chatów.
