---
stage: plan
bolt: 009-household-foundation-ui
status: accepted
created: 2026-09-23T07:22:20Z
---

# Plan implementacji: gęstość i responsywność ekranów gospodarstwa

## Cel

Poprawić wykorzystanie przestrzeni na ekranach gospodarstwa bez zmiany ich funkcji. Listy pozostaną szerokie, proste formularze otrzymają zwarty kontekst, a formularz dochodu wykorzysta szeroką, responsywną siatkę.

## Zakres

- Pasek aktywnego gospodarstwa, w tym selektor, rola i waluta.
- Lista członków oraz obszar formularza członka i relacji.
- Lista i formularz źródeł dochodu.
- Wspólny komponent panelu i reguły szerokości przycisków formularzy.
- Responsywność i wizualne testy regresji układu.
- Po późniejszej akceptacji uwagi projektowej: przeniesienie „Dostępów” do ustawień aktywnego gospodarstwa i otwieranie widoku danych zamiast uprawnień po wejściu do gospodarstwa.

Poza zakresem: zmiany API, danych, autoryzacji, pozostałej nawigacji oraz nowe moduły MVP.

## Podejście techniczne

1. Rozszerzyć współdzielony `Panel` o opcjonalną klasę układu. Usunąć zależność od ogólnego selektora `.panel > form`, aby szerokość formularza wynikała z jawnej klasy jego zadania.
2. Zmienić pasek kontekstu na siatkę z kolumną selektora ograniczoną do około `640px` i kolumną metadanych. Na wąskim ekranie elementy przejdą do jednego wiersza pełnej szerokości.
3. Zachować tabelę członków na pełnej szerokości. Obszar edycji pod tabelą ułożyć jako dwie kolumny: formularz członka oraz relacje. Przy braku miejsca kolumny ułożą się pionowo w kolejności DOM.
4. Dla formularza dochodu zastosować szeroki wariant i siatkę maksymalnie trzech kolumn. Przypisanie i opis otrzymają większy span, a pozostałe pola będą tworzyć zwarte grupy bez zmiany ich kolejności logicznej.
5. Ustawić przyciski wysyłające na szerokość treści w widoku desktopowym. Na małym ekranie dopuścić pełną szerokość dla wygodnego dotyku.
6. Oprzeć progi i odstępy na istniejącej skali 4 px oraz obecnych tokenach. Nie dodawać biblioteki ani nowych kolorów.

## Pliki przewidziane do zmiany

- `frontend/app/components/ui.tsx` — opcjonalna klasa układu panelu.
- `frontend/app/components/household-shell.tsx` — semantyczne klasy paska kontekstu.
- `frontend/app/components/members-panel.tsx` — dwukolumnowy obszar formularza członka i relacji.
- `frontend/app/components/income-panel.tsx` — szeroki wariant formularza i spany pól.
- `frontend/app/globals.css` — siatki, szerokości, przyciski i progi responsywne.
- `frontend/tests/records.spec.ts` — kontrola geometrii i braku przepełnienia na kilku szerokościach.

## Kryteria akceptacji

- [ ] Na widoku 1440 px selektor gospodarstwa nie rozciąga się bez potrzeby przez cały ekran, a rola i waluta pozostają czytelnie powiązane.
- [ ] Na szerokim widoku formularz członka i relacje wykorzystują dwie kolumny; tabela członków pozostaje pełnej szerokości.
- [ ] Formularz dochodu wykorzystuje do trzech kolumn na szerokim ekranie, dwie przy pośredniej szerokości i jedną na telefonie.
- [ ] Przyciski formularzy mają szerokość treści na desktopie i pełną szerokość na telefonie.
- [ ] Przy 1440×900, 1024×768 i 390×844 cała strona nie ma poziomego przepełnienia, treść i akcje nie są ucięte, a tabele zachowują kontrolowane przewijanie.
- [ ] Układ zachowuje logiczną kolejność odczytu i tabulacji, widoczne etykiety, `focus-visible`, stany disabled/loading/success/error oraz minimalny aktywny obszar 32×32 px.
- [ ] Istniejące testy funkcjonalne członków, relacji i dochodów przechodzą bez zmian kontraktu API.
- [ ] „Dostępy” są pod „Ustawieniami” wybranego gospodarstwa, a ponowne sprawdzenie uprawnień zachowuje aktywną sekcję.
- [ ] Prettier, ESLint, Stylelint, TypeScript i `scripts/quality.ps1` kończą się powodzeniem.

## Weryfikacja

- Automatyczne testy Playwright dla 1440×900, 1024×768 i 390×844, w tym pomiar szerokości kluczowych obszarów i brak przepełnienia dokumentu.
- Rzeczywisty przegląd ekranów członków i dochodów po przebudowie aplikacji oraz porównawcze zrzuty.
- Test obsługi klawiaturą i widocznego focusu dla selektora, pól i akcji.
- Pełna kontrola jakości projektu i ponowne uruchomienie istniejących testów UI.

## Zależności i kolejność

Plan zatwierdzony przez użytkownika poleceniem „kontynuuj pracę”. Implementacja rozpocznie się po zatwierdzeniu raportu testów i zamknięciu bolta 007. Po zakończeniu bolta 009 będzie można rozpocząć końcowy odbiór w bolcie 008.
