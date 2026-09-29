---
stage: test
bolt: 009-household-foundation-ui
status: approved
validated: 2026-09-23T20:23:56Z
created: 2026-09-23T08:22:53Z
---

# Raport testów: gęstość ekranów i ustawienia gospodarstwa

## Wynik

- **Testy UI:** 31/31 przeszło: 29 izolowanych scenariuszy Playwright oraz 2 rzeczywiste przepływy przez HTTPS, Django i PostgreSQL. Dwa scenariusze live były pominięte w przebiegu izolowanym i uruchomione osobno z flagą środowiskową.
- **Jakość i build:** produkcyjny build Next.js oraz `scripts/quality.ps1` przeszły; kontrola obejmuje Prettier, Ruff, ESLint, Stylelint i TypeScript.
- **Środowisko:** baza, backend i frontend są healthy; proxy działa, migracja zakończyła się kodem 0. Po testach nie pozostały konta ani gospodarstwa z prefiksem testowym.
- **Pokrycie procentowe:** nie było mierzone; wynik nie oznacza pełnego pokrycia aplikacji.

## Pliki testowe

- [x] `frontend/tests/records.spec.ts` — geometria przy 1440×900, 1024×768 i 390×844; kolumny formularza, szerokości akcji, lokalne przewijanie tabel, brak przewijania całej strony oraz dostępność klawiaturą i focus.
- [x] `frontend/tests/foundation.spec.ts` — ścieżka „Gospodarstwo → Ustawienia → Dostępy”, ekran startowy danych, zmiana gospodarstwa i zachowanie sekcji po ponownej kontroli uprawnień; dotychczasowe scenariusze kont i zaproszeń.
- [x] `frontend/tests/live-foundation.spec.ts` i `frontend/tests/live-records.spec.ts` — rzeczywiste tworzenie gospodarstwa, zaproszenia, ról, członka, relacji i dochodu oraz kontrola odczytu i audytu.

## Kryteria akceptacji

- ✅ **Selektor na szerokim ekranie:** przy 1440 px ma najwyżej 640 px szerokości, a rola i waluta pozostają w tym samym obszarze kontekstu.
- ✅ **Członkowie i relacje:** tabela zajmuje szeroki panel; formularz i relacje są obok siebie przy 1440 px oraz jeden pod drugim przy 1024 i 390 px.
- ✅ **Dochody:** siatka ma trzy kolumny przy 1440 px, dwie przy 1024 px i jedną przy 390 px; przypisanie i opis pozostają czytelnie szersze.
- ✅ **Akcje:** główne przyciski formularzy są zwarte na desktopie i pełnej szerokości na telefonie; „Zapisz rolę” w tabeli nie rozciąga się na całą komórkę.
- ✅ **Przepełnienie:** przy wszystkich trzech szerokościach strona nie ma poziomego przewijania. Tabele członków, dochodów i dostępów przewijają się we własnych obszarach; akcja dochodu jest dostępna po przewinięciu.
- ✅ **Klawiatura i focus:** do ustawień można przejść klawiszem Tab i otworzyć je Enterem; selektor, pole roli i akcja mają widoczny focus. Tabele można przewijać strzałkami.
- ✅ **Uprawnienia i stany:** istniejące testy Ownera, Administratora, Membera i Viewera oraz odmowy API przeszły. Po odświeżeniu uprawnień aktywne ustawienia pozostają otwarte.
- ✅ **Rzeczywisty stos i regresja:** oba przepływy live przeszły bez zmian kontraktu API; testy izolowane, build i kontrola jakości przeszły.

## Dowody wizualne

- 1440 px: [członkowie](evidence/after-members-1440.png), [dochody](evidence/after-income-1440.png), [ustawienia](evidence/after-settings-1440.png).
- 1024 px: [członkowie](evidence/after-members-1024.png), [dochody](evidence/after-income-1024.png).
- 390 px: [członkowie](evidence/after-members-390.png), [dochody](evidence/after-income-390.png).

Zrzuty obejrzano po wykonaniu testów. Na szerokości pośredniej i mobilnej tabela dochodów pokazuje część kolumn naraz, zgodnie z zamierzonym lokalnym przewijaniem; test potwierdza dostępność akcji po przewinięciu.

## Problemy wykryte i poprawione

- Po przeniesieniu „Dostępów” odświeżenie uprawnień wracało do widoku startowego. Zachowano wybraną sekcję w stanie sesji; test odmowy API potwierdza zachowanie ustawień.
- Pierwsza kontrola 1024 px błędnie wymagała limitu selektora 640 px także po przejściu paska kontekstu do jednej kolumny. Doprecyzowano pomiar: limit dotyczy szerokiego widoku, a na węższym selektor wykorzystuje dostępny wiersz.
- Przegląd zrzutu ustawień ujawnił zbyt szeroki przycisk „Zapisz rolę”. Zwężono go i dodano pomiar w teście.

## Checkpoint

Użytkownik zatwierdził raport testów. Bolt 009 i story 006 zakończono; można rozpocząć końcowy odbiór bolta 008.
