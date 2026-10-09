# Źródło przychodu — modal v2

Task poza ukończonym boltem 016; issue ISS-2026-002. Baza develop 63df3c6, branch fix/task-income-source-dialog.

## Zakres i pliki

- income-form.tsx: zastąpić dodatkowy blok CTA opcją w native select. Nie zapisywać sentinel jako source_id, nie zmieniać szkicu po otwarciu/anulowaniu.
- income-source-create.tsx: natywny dialog.showModal, istniejący rodzaj źródła, te same ContractForm/OtherSourceForm i endpointy co zarządzanie gospodarstwem. Domyślnie przypisanie z formularza przychodu, waluta gospodarstwa i data początku wybranego miesiąca; nigdy automatyczne utworzenie przychodu.
- other-source-form.tsx: opcjonalny compact mode tylko przy szybkim tworzeniu; sześć pól podstawowych (odbiorca, nazwa, kategoria, częstotliwość, początek, waluta); opcjonalne pola pod „Dodatkowe informacje”. Wszystkie wartości i reguły pełnego formularza pozostają dostępne. Otworzyć sekcję gdy API zwróci błąd ukrytego pola.
- contract-form.tsx: data końcowa „(opcjonalna)”, wskazówka „Puste pole oznacza umowę na czas nieokreślony”. Payload nadal null.
- globals.css: współdzielona powierzchnia modali; źródło max 760px, dwie kolumny, na 390px jedna; max wysokość i wewnętrzny scroll.
- tests: aktualizacja źródłowego CTA oraz test modala, fokusu, Escape, szkicu, walidacji i null end_date.

## Interakcja

Owner/Administrator w aktywnym miesiącu wybiera „+ Dodaj nowe źródło…” na końcu listy. Member/Viewer i zablokowany formularz nie dostają zapisu. W tle pozostaje dotychczasowy formularz. Modal jasny z granatowym tekstem i zielonym CTA. Domyślnie „Inne źródło”, możliwość wyboru „Umowa”; wymaganych pól umowy nie ukrywać. W modalu umowy można dodać firmę istniejącym zagnieżdżonym modalem.

Anuluj/Escape bez zmian zamyka modal; po zmianach inline potwierdzenie wewnątrz modala „Odrzucić szkic źródła?” z działaniami Anuluj/Odrzuć. Przy anulowaniu potwierdzenia powrót do formularza i fokus. Zapis/pending blokuje zamknięcie; błąd zachowuje wartości, błędy ukrytych pól otwierają szczegóły. Sukces odświeża opcje i wybiera źródło wyłącznie gdy pasuje do odbiorcy i okresu (istniejąca reguła); nie zmienia kwoty, waluty, daty/pliku przychodu. Źródło poza okresem nie będzie dostępne — istniejący komunikat.

Dialog ma nazwę, skupia fokus, ogranicza Tab do modala przez natywne showModal, Escape nie przenosi się do rodzica. Zamykanie przywraca fokus na select źródła. Brak zamknięcia kliknięciem backdrop, żeby nie gubić szkicu. CompanyDialog zachowuje niezależny top-layer i wraca do firmy. Zmiana rodzaju wymaga odrzucenia szkicu, potem reset dirty dla nowego pustego formularza.

## Makieta i bramka

Wersja v2: evidence/ui-design/prototype.html oraz desktop.jpg, mobile.jpg, contract.jpg, contract-mobile.jpg, details.jpg, error.jpg, pending.jpg, discard.jpg, company.jpg. Dane syntetyczne. Makieta pokazuje kompaktowy modal, pełne pola umowy, opcjonalne szczegóły, etykietę end_date i listę z akcją. Przed kodem wymagany review.md z accepted i Score >7.5 dla obu rodzajów.

## Weryfikacja

Nie modyfikować lokalnych plików użytkownika. Formatter/lint po każdym źródle, scripts/quality.ps1, sensowne Playwright (mock API do interakcji) oraz build. Potwierdzić dialog/fokus/szkic na 1440/390. Koniec taska: commit tylko własnych plików, osobny review końcowy; integracja i lokalny rebuild zgodnie z autoryzacją projektu.
