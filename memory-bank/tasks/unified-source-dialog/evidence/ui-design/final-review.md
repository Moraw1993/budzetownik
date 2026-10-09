# Niezależny odbiór implementacji — unified-source-dialog

Recenzent: `/root/review_unified_sources`, 2026-10-09. Decyzja: **accepted**. Brak otwartych problemów blokujących w ocenionym zakresie.

Zakres: dwa wskazane okna TWORZENIA źródła (Zarządzanie rodziną / Okresy i przychody), wspólny komponent `IncomeSourceCreate`, wariant innego źródła i umowy. Historyczna edycja/archiwizacja istniejącego źródła pozostaje osobną operacją. Ten raport nie ocenia nowego bolta ani wydania.

## Rzeczywiście obejrzane dowody

Obejrzano wszystkie 12 obrazów `actual-family-{1920,1440,1366,390}.jpg`, `actual-income-{1920,1440,1366,390}.jpg`, `actual-contract-{1920,1440,1366,390}.jpg`. Są to renderingi produkcyjnego frontendu na lokalnym preview `http://127.0.0.1:8098`, z syntetycznym API. Obrazy użytkownika przy 60% nie były dowodem ergonomii.

Rodzinne oraz przychodowe wejście mają rzeczywiście ten sam tytuł, opis, kolejność i układ pól, dodatkowe informacje, szerokość, przyciemnienie i przyciski. Jedyną widoczną różnicą danych jest dopuszczona podpowiedź daty z miesiąca przychodu. Obrazy 1920×950 i 1440×800 pokazują całe rozwinięte formularze; 1366×650 i 390×740 pokazują realne przewinięcie wewnętrzne do ostatnich pól. Opis, data końca umowy i akcja zapisu nie są ucięte ani zasłonięte. Przy mniejszej wysokości pola powyżej przesuwają się za granicę obszaru przewijania; nagłówek, wybór rodzaju i zapis pozostają widoczne. Nie jest to usunięcie pól.

## Oceny pięciu kryteriów

Każdy Score jest średnią pięciu ocen z równymi wagami, przed zaokrągleniem.

| Widok | Użyteczność/wymagania | Hierarchia | Spójność | Dostępność | Responsywność/stany | Score | Decyzja |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| family-1920 / family-1440 | 9 | 9 | 9 | 8.5 | 8.5 | 8.8 | accepted dla każdego |
| income-1920 / income-1440 | 9 | 9 | 9 | 8.5 | 8.5 | 8.8 | accepted dla każdego |
| family-1366 / income-1366 | 9 | 8.5 | 9 | 8.5 | 8.5 | 8.7 | accepted dla każdego |
| family-390 / income-390 | 8.5 | 8.5 | 9 | 8.5 | 8.5 | 8.6 | accepted dla każdego |
| contract-1920 / contract-1440 | 8.5 | 8.5 | 9 | 8.5 | 8.5 | 8.6 | accepted dla każdego |
| contract-1366 / contract-390 | 8.5 | 8 | 9 | 8.5 | 8.5 | 8.5 | accepted dla każdego |

Użyteczność poprawia wspólne okno zamiast długiego inline formularza; hierarchię poprawia rozdzielenie stałych akcji od przewijanych pól. Spójność potwierdzają ten sam komponent, wspólne pola i właściwa typografia/paleta działającej aplikacji. Dostępność obejmuje widoczne etykiety, fokus, osiągalne przyciski, opcjonalny koniec umowy i odsłanianie błędów. Responsywność nie bazuje na pomniejszaniu tekstu: pełny rozwinięty widok mieści się na dużym desktopie, a niższe i mobilne okna mają lokalny scroll. To nie jest pełny audyt WCAG.

## Przegląd kodu i zachowania

- `OtherSourcesPanel` przy tworzeniu montuje `IncomeSourceCreate`; `IncomeForm` używa tego samego komponentu. Nie ma drugiego formularza tworzenia w rodzinie. Osobne wywołanie niekompaktowego `OtherSourceForm` jest ograniczone warunkiem `editing`.
- Wspólny komponent przyjmuje gospodarstwo, osoby i opcjonalną datę; brak zależności od okresu w rodzinie. Obsługuje oba rodzaje przez te same formularze, zachowując właściwe endpointy, opcjonalny koniec umowy, precyzję kwot i brak tworzenia przychodu przy dodaniu źródła.
- Zapis z rodziny zamyka okno i wywołuje `reloadSources`; `FamilyPanel` odświeża źródła i liczniki. Przy umowie tekst wskazuje zakładkę Umowy; sam kontrakt nie jest błędnie dodawany do tabeli innych źródeł.
- Początkowy fokus i jego powrót, blokada pending, potwierdzenie dirty, Escape i zagnieżdżony dialog firmy zachowane. `fieldset disabled` zachowuje semantykę blokady mimo `display:contents`; nie zastąpiono jej samą wizualną klasą.
- Scroll jest ograniczony do `.source-fields` / `.source-contract-fields`; przyciski są poza nimi. CSS nie wprowadza zoom, transform/scale ani pomniejszania fontu. Podstawowy i rozwinięty układ z obu wejść porównywany jest w testach wraz z etykietami i geometrią.

## Niezależnie uruchomione testy

Recenzent sam uruchomił testy przeciw lokalnemu produkcyjnemu preview z mock API i oddzielnymi katalogami wyniku `.runtime/reviewer-unified-source-*`:

- `records.spec.ts`: **8 PASS** — zapis źródła, precyzja, edycja/archiwizacja, Member/Viewer bez akcji, zmiana uprawnień, paginacja, stale-response i klawiatura.
- `periods-recovery.spec.ts`: **6 PASS** — w tym blokada nawigacji i disabled pól podczas trwającego zapisu źródła.
- `unified-source-dialog.spec.ts`, `household modal saves...`: **1 PASS** — pełny zapis z rodzinnego wejścia, powrót fokusu, odświeżony wiersz, brak nowego przychodu.
- `income-source-dialog.spec.ts`, `hidden field API errors...`: **1 PASS** — odsłonięcie sekcji z błędem bez utraty szkicu.

Łącznie **16 niezależnie wykonanych testów PASS**. Testy syntetycznego API weryfikują interfejs; nie są dowodem nowego live testu backendu. Pozostałe testy geometrii/fokusu/nested firmy odczytano i zestawiono z obrazami, ale w tej recenzji nie deklaruję ich własnego reruna. Build, pełna kontrola jakości i pełny rerun autora są osobnymi dowodami autora i nie zostały tutaj podmienione na niezależne PASS.

Osobno autor przekazał końcowy wynik dla checkpointu kodu `8f3e2e1`: pełny przebieg dziewięciu plików **81 PASS, 2 SKIP, exit 0** (sesja 55928), w tym wszystkie dziewięć testów unified; kontrola jakości PASS (20863), build PASS. Wyniki opisuje `implementation-walkthrough.md`. Pominiętych testów nie wliczam do PASS. Te wyniki są dowodami autora; 16 wyników powyżej zostało wykonanych przez recenzenta.

Autor zgłosił wcześniejszy pojedynczy błąd `scrollIntoViewIfNeeded` pozostawiający 1 px opisu poza obszarem na 1366. Odczytany aktualny test dodaje zwykłe przewinięcie kółkiem po hover i nadal wymaga `ratio:1`, a aktualne fotografie pokazują w całości ostatnie pole nad przyciskiem. Nie osłabiono asercji ani nie uznano częściowej widoczności za pełną. Autor potwierdził końcowy pełny rerun bez błędów.

## Granice akceptacji

Implementacja spełnia zaakceptowany projekt oraz poprawia konkretną różnicę dwóch okien wskazaną przez użytkownika. Bez otwartych blockerów UI lub regresji wykrytych w niezależnych 16 testach. Integracja może nastąpić po domknięciu pełnych wymaganych kontroli przez autora; nie deklaruję na podstawie tego raportu wdrożenia ani merge.
