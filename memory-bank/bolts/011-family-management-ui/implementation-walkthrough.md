---
stage: implement
bolt: 011-family-management-ui
created: 2026-09-26T20:05:44Z
status: awaiting-validation
---

# Przegląd implementacji: Zarządzanie rodziną

## Podsumowanie

Zastąpiono osobne działy członków i dochodów działem „Zarządzanie rodziną”. Osoby pokazują przypisane umowy i inne źródła, a źródła całego gospodarstwa mają własny obszar. Dodano osobne formularze firm, umów i innych źródeł oraz jawną konwersję istniejącego źródła w umowę.

## Organizacja

Istniejąca powłoka gospodarstwa utrzymuje wybór gospodarstwa i sekcji. Kompozycja rodziny pobiera wspólne dane osób i źródeł oraz przekazuje je panelom. Panel członków zachowuje dotychczasowe zarządzanie osobami i relacjami, a nowe panele rozdzielają słownik firm, umowy i inne źródła. Wszystkie zapisy korzystają z istniejącego klienta sesji/CSRF i wspólnych kontrolek formularzy.

## Wykonana praca

- [x] `frontend/app/components/application.tsx` i `household-shell.tsx` — jedna pozycja nawigacji „Zarządzanie rodziną” z zachowaniem wybranego gospodarstwa.
- [x] `frontend/app/components/family-panel.tsx` — wspólny odczyt osób i źródeł, odświeżanie po zmianach oraz anulowanie nieaktualnych odczytów.
- [x] `frontend/app/components/members-panel.tsx` — źródła przy każdej osobie, stan pusty i oznaczenie archiwum przy zachowaniu formularzy osób.
- [x] `frontend/app/components/other-sources-panel.tsx` — źródła osób i całego gospodarstwa, opcjonalna podpowiedź miesięczna, edycja, archiwizacja i rozpoczęcie jawnej konwersji.
- [x] `frontend/app/components/company-panel.tsx` — słownik firm z tworzeniem, zmianą nazwy i archiwizacją.
- [x] `frontend/app/components/contract-form.tsx` i `contract-panel.tsx` — formularz i lista umów, kwota brutto z podstawą, edycja, archiwizacja, dobór firmy podczas wypełniania i konwersja z wersją źródła.
- [x] `frontend/app/lib/api.ts` — oddzielne warianty typów umowy i innego źródła, opcjonalna kwota oraz kody błędów konfliktu.
- [x] `backend/households/services.py` — ochronę ostatniego aktywnego Ownera oraz historię poprzedniej i nowej roli.
- [x] `backend/households/record_services.py`, `record_serializers.py` i `family_income_services.py` — wymaganie aktualnej wersji przy edycji źródła oraz umowy.
- [x] `backend/households/exceptions.py` i `backend/config/settings.py` — rozróżnialne kody konfliktu Ownera i źródła w odpowiedziach API.
- [x] `backend/households/tests/test_api.py`, `test_records.py`, `test_family_income_api.py`, `test_concurrency.py` i `test_family_income_concurrency.py` — regresja ochrony Ownera, historii dostępu, wersji i równoległych zapisów.
- [x] `frontend/app/globals.css` — lista źródeł przy osobie i dopasowanie formularzy oraz nawigacji do układu mobilnego.
- [x] `frontend/tests/records.spec.ts` — uzupełnienie typu istniejącej syntetycznej próbki źródła; scenariusze testowe nowego działu należą do etapu 3.
- [x] Usunięto nieużywany `frontend/app/components/income-panel.tsx` po przeniesieniu funkcji innych źródeł do osobnego panelu.

## Główne decyzje

- **Jeden odczyt źródeł na poziomie rodziny:** pozwala pokazać tę samą tożsamość źródła przy osobie i w części gospodarstwa bez kopiowania danych i logiki HTTP.
- **Oddzielne formularze `other` i `contract`:** rozróżniają opcjonalną podpowiedź od kwoty brutto oraz właściwe pola i endpointy. Żaden zapis UI nie tworzy przychodu miesięcznego.
- **Osobny formularz firmy:** dodanie firmy nie powoduje zagnieżdżenia formularzy ani wyczyszczenia pól umowy. Nowa firma jest wybierana w trwającym formularzu.
- **Konflikt wersji:** przy nieaktualnej wersji formularz konwersji lub edycji umowy zamyka się, lista jest odświeżana, a użytkownik dostaje wyraźny komunikat.
- **Konflikt źródła:** edycja innego źródła przekazuje jego wersję; po konflikcie odświeża dane i wymaga ponownego wyboru. Klient rozpoznaje kod błędu API, więc ochrona Ownera ma inny komunikat.

## Zmiany względem planu

### Aktualny kierunek wizualny — 29 września 2026

Obowiązuje jasny design v3 z wątku „Zaproponuj 3 widoki zarządzania” (ID `01a0df63-b2ca-7872-8447-983e623be6a4`), potwierdzony przez użytkownika podczas kontynuacji bolta. Jasne tło, białe panele, zielone akcje i granatowa nawigacja są wspólnym standardem całej aplikacji, zgodnie z [design-system.md](../../standards/design-system.md). Nie przywracać wcześniejszego ciemnego motywu ani osobnego motywu dla rodziny.

- [x] Moduł rodziny ma osobne zakładki „Członkowie”, „Źródła dochodu” i „Umowy”, rzeczywiste liczniki oraz nawigację klawiaturą.
- [x] Członkowie są prezentowani w kartach; formularze i słowniki otwierają się na żądanie. Dodanie firmy z umowy korzysta z modalu i zachowuje dane umowy.
- [x] Wspólna jasna paleta obejmuje również ustawienia, dostępy, tworzenie gospodarstwa, logowanie, pierwsze konto i zaproszenia.

[Raport kontroli wizualnej v3](../../../design-qa.md) i przywołany wątek opisują oceny 8,0/10 dla koncepcji oraz 8,1/10 dla wdrożenia. Są to wyniki wcześniejszej recenzji na danych demonstracyjnych, a nie pełny odbiór funkcjonalny bolta. Etap testów nadal musi potwierdzić rzeczywiste przepływy API, role, archiwizację, izolację gospodarstw, klawiaturę i szerokości 1440, 1024 oraz 390 px w aktualnym jasnym designie.

Kontynuacja odbywa się na branchu `feat/bolt-011-family-management-ui`, utworzonym z `chore/task-ai-dlc-git-workflow`, ponieważ obecny kod bolta i zmiany wizualne są dostępne w tym checkoutcie. Zastane niezacommitowane zmiany w raporcie wizualnym, design systemie, wspólnych stylach i shellu pozostają poza commitem dokumentacji.

Podczas tej kontynuacji `scripts/quality.ps1` przeszedł po udostępnieniu lokalnego Dockera (Ruff, Prettier, ESLint, Stylelint i TypeScript); produkcyjny build Next.js również przeszedł. Nie wykonywano ponownie testów backendu ani zapisów w rzeczywistej bazie. Etap implementacji nadal oczekuje na zatwierdzenie przed etapem testów.

Istniejący panel dochodów został zastąpiony panelem innych źródeł, ponieważ dawny formularz mieszał źródła z nowymi umowami i wymagał obowiązkowej podpowiedzi kwoty. Mechanizm formularzy, klienta API, stylów i zarządzania osobami pozostał współdzielony.

Po audycie z 26 września rozszerzono etap o poprawki backendu z ukończonych wcześniej boltów: aktywny Owner, wersjonowanie edycji oraz pełniejszą historię dostępu. Nie zmieniono schematu bazy danych.

## Zależności

Nie dodano bibliotek ani usług.

## Sprawdzenie i dalszy etap

Build produkcyjny Next.js i `scripts/quality.ps1` przeszły po ostatnich poprawkach. Pełny zestaw Django przeszedł 83/83 na odrębnej bazie PostgreSQL po poprawkach API. Etap 3 obejmie dostosowanie starych scenariuszy nawigacji, nowe testy przepływów i ocenę widoków na szerokim oraz mobilnym ekranie.

Działająca instalacja ma nadal migracje tylko do `0003`; migracja `0004` i nowe API nie są tam wdrożone. Nie wykonywano zapisów testowych na tej instalacji.
