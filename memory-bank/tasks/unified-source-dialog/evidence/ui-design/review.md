# Niezależna ocena projektu v1 — unified-source-dialog

Recenzent: `/root/review_unified_sources`, 2026-10-09.
Decyzja: **accepted** dla projektu v1. To akceptacja projektu przed implementacją, nie odbiór działającej aplikacji.

Przeczytano `implementation-plan.md`, `prototype.html`, standard `ui-design-review.md` i `design-system.md`. Rzeczywiście obejrzano wszystkie siedem JPEG w tym katalogu. Ocena dotyczy dwóch wejść DODAWANIA źródła, wspólnego modalu oraz jego wariantu umowy. Historyczna edycja istniejącego źródła nie jest tym oknem i nie stanowi dowodu jego ujednolicenia.

## Wyniki poszczególnych widoków

Kolumny ocen: użyteczność i wymagania; hierarchia i czytelność; spójność; dostępność; responsywność i stany. Score jest średnią pięciu ocen z równymi wagami, przed zaokrągleniem.

| Wizualizacja | Użyteczność | Hierarchia | Spójność | Dostępność | Responsywność/stany | Score | Decyzja |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| family-1920.jpg | 9 | 9 | 8.5 | 8 | 8 | 8.5 | accepted |
| income-1920.jpg | 9 | 9 | 8.5 | 8 | 8 | 8.5 | accepted |
| family-expanded-1920.jpg | 9 | 8.5 | 8.5 | 8 | 8 | 8.4 | accepted |
| income-expanded-1920.jpg | 9 | 8.5 | 8.5 | 8 | 8 | 8.4 | accepted |
| contract-1920.jpg | 8.5 | 8.5 | 8.5 | 8 | 8 | 8.3 | accepted |
| contract-1366.jpg | 8.5 | 8.5 | 8.5 | 8 | 8 | 8.3 | accepted |
| mobile.jpg | 8.5 | 8 | 8.5 | 8 | 8 | 8.2 | accepted |

## Uzasadnienie

- **Użyteczność i wymagania:** rodzinne i przychodowe wejście mają identyczny modal: tytuł, opis, rodzaj źródła, kolejność sześciu podstawowych pól, sekcję dodatkową i przyciski. Różni się kontekst za przyciemnieniem. Tak samo jest na obu rozwiniętych wizualizacjach. Rodzina nie ma rozciągającego stronę formularza tworzenia. Wariant umowy pokazuje opcjonalną datę końca wraz z jednoznacznym opisem czasu nieokreślonego.
- **Hierarchia i czytelność:** trzy kolumny na desktopie ograniczają wysokość bez pomniejszania pól i tekstu. Nagłówek i zapis pozostają odrębne od przewijanych pól. Podstawowy modal zajmuje około 550 px wysokości; rozwinięty około 730 px i cały mieści się w 1920×950. Regularność jest obok dwuwierszowego opisu. Umowa także mieści się w tym viewportcie. Telefon ma jedną kolumnę i czytelne etykiety. Przed decyzją ponownie obejrzano wszystkie siedem obrazów po aktualizacji `.source-extra-notes` przez autora.
- **Spójność:** biała powierzchnia, zielony zapis/fokus, granatowy tekst i przyciemnienie zachowują system aplikacji. Makieta używa Arial zamiast docelowego Geist, więc końcowy odbiór musi dotyczyć rzeczywistej typografii. To ograniczenie wierności prototypu, nie powód do zmiany wspólnego fontu aplikacji.
- **Dostępność:** widać etykiety, początkowy fokus, Anuluj i zapis o odpowiednich rozmiarach. Natywny dialog ma nazwę dostępną, plan obejmuje klawiaturę, powrót fokusu, potwierdzenie utraty szkicu, blokadę pending i tekstowe błędy. Prototyp nie dowodzi wszystkich tych zachowań; wymagają testów kodu. Nie deklaruję pełnego audytu WCAG.
- **Responsywność i stany:** przy 1366×650 nagłówek, rodzaj i zapis mieszczą się, a dolne pola umowy mają własny scroll. Na 390×740 stały przycisk nie przesuwa się poza ekran; pola są przewijane wewnątrz. Dolne pola niewidoczne na pojedynczym zdjęciu nie mogą zostać pominięte w implementacji. Prototyp zawiera wszystkie pola, opakowuje je w `.source-fields` z `overflow-y:auto`, a CTA pozostawia poza tym obszarem. Nie ma CSS zoom/scale. Zdjęcia użytkownika przy 60% nie zostały wykorzystane jako dowód zmieszczenia formularza.

## Braki blokujące

Nie stwierdzono blokujących braków projektu. Wszystkie Score są ściśle większe od 7.5. Wolno wdrożyć ten konkretny układ.

## Obowiązkowa weryfikacja po implementacji

1. Porównać rzeczywiste **oba wejścia**, nie tylko modal przychodu, przy zoom 100% i deviceScaleFactor 1. Sprawdzić 1920×950, 1440×800, 1366×650, 390×740 oraz rozwinięte szczegóły i wariant umowy.
2. Przewinąć do ostatniego pola na małym ekranie; pole i opis muszą pozostawać całkowicie osiągalne ponad CTA, bez poziomego overflow, także po błędzie i z długą nazwą źródła. Zapisać dowód po przewinięciu, nie tylko początek formularza.
3. Nagłówek/Anuluj/zapis nie mogą zniknąć. Zachować wszystkie pola, walidację, podpowiedź opcjonalności końca umowy i widoczne błędy; jeśli błąd dotyczy zwiniętych szczegółów, odsłonić je i przewinąć do błędu.
4. Zweryfikować dirty/pending/error, Escape, Tab/Shift+Tab, powrót fokusu do odpowiedniego przycisku lub listy, nested CompanyDialog oraz zachowanie szkicu i załączników przychodu. Zapis źródła w rodzinie musi odświeżyć dane; zapis umowy nie może udawać nowego wiersza w tabeli innych źródeł.
5. Dowód funkcjonalnej zgodności tworzenia ma pokazać ten sam komponent i układ. Sam fakt wspólnych DTO lub API jest niewystarczający.

Próba dodatkowego niezależnego pomiaru prototypu Playwright w sandboxie nie wystartowała: domyślna wersja Chromium była niedostępna, a istniejąca lokalna przeglądarka nie mogła zostać uruchomiona w sandboxie. Nie przedstawiam tego jako PASS; powyższa bramka opiera się na rzeczywiście obejrzanych wizualizacjach i odczytanym prototypie. Geometria oraz interakcje działającej aplikacji pozostają obowiązkiem odbioru po kodzie.
