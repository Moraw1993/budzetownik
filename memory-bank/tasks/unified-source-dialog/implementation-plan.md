# Ten sam formularz dodawania źródła — v1

Baza develop09eafea777f4fde5614f8e7d7ca0b73a91a0cdd9, branch fix/task-unified-source-dialog. Ponowne zgłoszenie ISS-2026-002: poprzedni task pozostawił odmienny, bardzo długi formularz dodawania w rodzinie. Wspólne dane/kod nie spełniały żądania identycznego interfejsu. Zdjęcia użytkownika1/2 wykonane przy60%,3przy100%; nie traktować pomniejszonych zrzutów jako dowodu ergonomii.

## Wiążący wynik

Zarządzanie rodziną → Źródła dochodu → Dodaj źródło i Okresy i przychody → Źródło dochodu → Dodaj nowe źródło otwierają TEN SAM IncomeSourceCreate: tytuł, rodzaj, identyczna kolejność i układ pól, dodatkowe informacje, Anuluj, zapis, tło i wymiary. Różnice wyłącznie podpowiedzi kontekstu (odbiorca, miesiąc) i czynność po zapisie. Nie pozostawiać inline formularza tworzenia w rodzinie. Edycja istniejącego źródła pozostaje osobnym istniejącym przepływem z wersjonowaniem/archiwizacją; ten task naprawia dwa wskazane okna DODAWANIA.

## Pliki i odpowiedzialności

- income-source-create.tsx: usunąć zależność od PeriodContext, przyjąć Household, members i opcjonalną podpowiedź daty. Obsługiwać identyczny rodzaj other/contract w obu wejściach. onSaved zwraca id+kind, onPendingChange opcjonalne. Pusta data końca nadal null. Nie duplikować okien ani kodu formularzy.
- income-form.tsx: przekazać household i month_start do wspólnego okna; zachować szkic, pliki i filtrowanie źródła.
- other-sources-panel.tsx: tworzenie przez wspólny modal, pełny stary panel wyłącznie przy editing. Tabela pozostaje w tle. Sukces odświeża źródła i liczniki; umowa ma komunikat wskazujący zakładkę Umowy. Dotychczasowa edycja/konwersja/archiwizacja zachowane. refreshAccess z istniejącego gospodarstwa.
- other-source-form.tsx i contract-form.tsx: obszar pól jako kontrolowany wewnętrzny scroll tylko w modalu. Nie zmniejszać globalnego fontu, wysokości kontrolek, nie ustawiać zoom/transform/scale. Źródło ma sześć podstawowych pól; szczegóły z tymi samymi wszystkimi polami.
- globals.css: modal max920px, trzy kolumny desktop >=900, dwie600–899, jedna<600. Nagłówek i przyciski dostępne; scroll pól wewnątrz okna, bez przesuwania całej strony. Zwarta opcjonalna sekcja: trzy pola w rzędzie, opis2wiersze, regularność obok opisu. Wymagane pola umowy nie są ukrywane.

## Akceptacja ergonomii

Browser zoom100%, deviceScaleFactor1, żadnego CSSzoom. Przegląd obu wejść przy1920x950 (monitor1920x1080 z miejscem na pasek przeglądarki),1440x800,1366x650 oraz390x740. Podstawowy formularz ma mieścić się na desktopie; rozwinięte wszystkie dane mają mieścić się przy1920x950. Na mniejszych viewportach wewnętrzny scroll pól, a zapis i anulowanie pozostają widoczne, osiągalne i nie zasłaniają pól. Żadnego poziomego overflow.

Przejścia: pristine Escape/Anuluj → zamknięcie; dirty → potwierdzenie i zachowanie szkicu; pending → blokada zamknięcia; błąd → tekst i zachowanie danych, automatyczne odsłonięcie szczegółów. Fokus początkowy, Tab/Shift+Tab i powrót do różnych właściwych triggerów. CompanyDialog nadal niezależnie powyżej umowy. Owner/Administrator tworzą, Member/Viewer nie widzą akcji.

## Dowody i kolejność

Makieta v1 w evidence/ui-design z obrazami family/income w zwykłej skali, obu z rozwiniętymi szczegółami, modal umowy i niska wysokość. Osobny reviewer musi porównać OBIE ścieżki, nie tylko modal przychodu. Po accepted Score>7.5 implementacja, formatter/lint, scripts/quality.ps1, testy porównujące pola/układ/wysokość/zoom100%, test zapisu rodziny i zachowania szkicu przychodu, obrazy rzeczywiste, final review. Scopedcommity, integracja develop, główny lokalny frontend. Bez release/017 i bez zastanych zmian użytkownika.
