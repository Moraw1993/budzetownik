# Zarządzanie rodziną — kontrola wizualna

final result: passed

## Materiał porównawczy

- Wzorzec: `.runtime/selected-family-ui.png` (1487 × 1058 px), obraz wybrany przez użytkownika.
- Wdrożenie: `.runtime/ui-members.jpg` (1189 × 884 px), przeglądarka aplikacji Codex, `http://127.0.0.1:4173/`, stan: zakładka Członkowie, formularze zamknięte.
- Widoki dodatkowe: `.runtime/ui-sources.jpg` i `.runtime/ui-contracts.jpg` (oba 1189 × 884 px).
- Pełny widok wzorca i wdrożenia został otwarty obok siebie na `http://127.0.0.1:4173/preview-comparison`. Porównanie skaluje oba obrazy do równej szerokości, bez zmiany proporcji. Źródłowy kadr jest szerszy i wyższy od dostępnego kadru przeglądarki; różnicę wysokości i wynikające z niej zawijanie tekstu uwzględniono przy ocenie.
- Gęstość: obrazy mają pojedynczą rozdzielczość, bez normalizacji `@2x`. CSS viewport przeglądarki raportował 1254 × 884 px, a zapisany obraz miał 1189 × 884 px. Narzędzie przeglądarki nie zastosowało próby ustawienia dokładnie 1487 × 1058 px.
- Nie tworzono oddzielnego porównania przyciętych fragmentów: pełny widok pokazuje całą hierarchię, nawigację, nagłówek i tabelę. Tekst oraz formularze sprawdzono dodatkowo w natywnych widokach każdej zakładki.

## Ustalenia

- Brak otwartych usterek P0, P1 lub P2 w docelowym widoku desktopowym.
- Typografia: użyty font Geist Variable, zbliżona hierarchia tytułu, nagłówka sekcji i drobnych etykiet. Zawijanie opisów różni się ze względu na dostępny kadr.
- Układ: zachowane główne proporcje — nawigacja aplikacji, nagłówek, pionowe menu modułu i pojedynczy aktywny panel. Formularze i słowniki otwierają się na żądanie, więc ekran początkowy pozostaje czytelny.
- Kolory: granatowe tło i panele, niebieski stan aktywny oraz przycisk główny odpowiadają wzorcowi; kontrast tekstu i widoczny fokus klawiatury pozostają czytelne.
- Obrazy i ikony: wzorzec nie zawiera fotografii ani ilustracji. Ikony interfejsu pochodzą z biblioteki Lucide i pasują do istniejącego systemu aplikacji.
- Treść: nazwy trzech zakładek i główne działania są zgodne z makietą. Opis członków, dodatkowy przycisk tworzenia gospodarstwa oraz informacje o źródłach dochodu pochodzą z istniejących funkcji produktu.

## Interakcje i ograniczenia

- W przeglądarce sprawdzono przełączanie trzech zakładek, otwieranie formularzy członka, źródła i umowy, przeniesienie fokusu do pierwszego pola, dodanie firmy z formularza umowy oraz przejście ze źródła dochodu do formularza przekształcenia. Nie stwierdzono błędów w konsoli.
- Podgląd korzysta z przykładowych danych lokalnych. Nie wykonywano zapisu do prawdziwej bazy; istniejące wywołania API pozostają w kodzie aplikacji.
- Przeglądarka nie zastosowała wymiaru 390 × 844 px, więc wygląd mobilny oceniono na podstawie reguł responsywnych CSS, bez wiarygodnego zrzutu ekranu. Jest to luka w weryfikacji, nie stwierdzona usterka.

## Historia poprawek

1. W pierwszym podglądzie wiersz członka był zbyt ciasny: działanie archiwizacji przeniesiono do formularza edycji, a szczegóły źródła pod nazwę osoby. Po ponownym otwarciu widok `.runtime/ui-members.jpg` pokazuje czytelny wiersz i dostępne działanie Edytuj.
2. Przy węższym desktopowym kadrze akcja zakładki źródeł zawijała się pod opis; poprawiono układ nagłówka. Zrzut `.runtime/ui-sources.jpg` pokazuje przycisk obok nagłówka.
3. Otwarte formularze pojawiały się poza widoczną częścią strony; dodano fokus pierwszego pola. Ponowna kontrola potwierdziła fokus dla członka, źródła, umowy i firmy.

## Dalsze dopracowanie

- [P3] Jeśli użytkownicy często pracują na ekranach około 1250 px, warto rozważyć układ kart dla szerokich tabel źródeł i umów. Teraz tabele mają jawne przewijanie poziome i pozostają dostępne z klawiatury.
- Powtórzyć oględziny przy rzeczywistym mobilnym viewport, gdy sterowanie wymiarami przeglądarki będzie działać.
