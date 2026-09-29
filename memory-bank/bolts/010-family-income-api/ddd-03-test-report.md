---
unit: 001-family-income-api
bolt: 010-family-income-api
stage: test
status: awaiting-validation
updated: 2026-09-26T20:24:04Z
---

# Raport testów: API firm, umów i źródeł dochodu

## Wynik

- **Pełny zestaw Django:** 80/80 testów przeszło na oddzielnej bazie PostgreSQL. Obejmuje 12 nowych testów bolta 010 oraz 68 wcześniejszych testów regresyjnych.
- **Kontrola jakości:** `scripts/quality.ps1` przeszła: Ruff, Prettier, ESLint, Stylelint i TypeScript bez błędów. Django nie wykrywa dodatkowych zmian migracji (`makemigrations --check`).
- **Pokrycie:** 97% łącznie dla pięciu zmienionych modułów wykonawczych, zmierzone przez `coverage` z analizą gałęzi podczas 60 testów gospodarstw. Próg >80% jest spełniony.
- **Wydajność:** 6/6 serii operacji firm i umów spełniło `P95 < 500 ms` przy 1 oraz 5 równoczesnych klientach, po 20 rozgrzewkach i 200 próbach na serię. Nie było błędnych odpowiedzi.

## Środowisko i metoda

Testy działały w odrębnym projekcie Docker `bolt010-test`, z PostgreSQL 17 i syntetycznymi danymi. Nie wykonywano migracji ani operacji testowych na bieżącej instalacji użytkownika. Test migracyjny użył `MigrationExecutor`: cofnął schemat gospodarstw do `0003`, zapisał stare źródła i audyt, zastosował `0004_family_income`, a potem porównał rekordy.

Pomiar P95 użył `APIClient` w procesie Django i PostgreSQL w osobnym kontenerze przez sieć Docker. Obejmuje obsługę żądania w Django i bazę, ale nie obejmuje HTTPS, reverse proxy ani Gunicorna. Host kontenera: Linux/WSL2, 16 logicznych CPU. P95 obliczono metodą najbliższej rangi. Przed pomiarem przygotowano 81 firm, 81 członków i 80 umów; po próbach zapisu było 520 umów i 520 źródeł. Dane były wyłącznie syntetyczne.

## Kryteria historii

- ✅ **001-company-dictionary:** nazwa jako jedyne wymagane pole; ponowne użycie firmy w wielu umowach; role Owner/Administrator do zapisu, Member/Viewer do odczytu; obce identyfikatory odrzucone; archiwizacja zachowuje umowy i audyt, blokując nowe powiązania.
- ✅ **002-contract-sources:** aktywny członek i firma z tego samego gospodarstwa; cztery typy umów, trzy podstawy brutto, stanowisko tylko przy pracy/zleceniu, nazwa własna typu „inne”; wiele umów jednego członka; nieujemny `Decimal(18,2)`, daty i waluta walidowane; zapis/edycja/archiwizacja atomowe z audytem. Brutto nie trafia do `default_monthly_amount` i nie tworzy przychodu miesiąca.
- ✅ **003-other-sources:** źródło członka albo gospodarstwa, opcjonalna podpowiedź miesięczna, brak szczegółów umowy, odrzucenie jednorazowego regularnego źródła. Stary endpoint odczytuje rodzaj, właściciela i status oraz zachowuje dotychczasowe pola dawnych źródeł.
- ✅ **004-legacy-source-migration:** dwa rekordy starego schematu zachowały UUID, gospodarstwo, członka, kwoty, daty, walutę, status i audyt. Oba otrzymały `kind=other`, nie powstała firma, umowa ani przychód miesięczny. Jawna konwersja zachowuje UUID, zapisuje stan przed/po i wycofuje całość przy błędzie audytu, walidacji lub konflikcie wersji.

## Testy bezpieczeństwa i współbieżności

- Brak sesji i brak CSRF blokują dostęp lub zapis. Owner i Administrator zapisują; Member i Viewer odczytują. Użytkownik spoza gospodarstwa oraz bezpośrednie obce identyfikatory firmy i umowy nie ujawniają danych.
- Obcy członek lub firma w żądaniu tworzenia są odrzucani. Archiwalne obiekty pozostają czytelne jako historia, ale nie tworzą nowych powiązań.
- Testy na PostgreSQL uruchomiły równolegle edycję starego źródła i konwersję: dokładnie jedna operacja się powiodła, druga otrzymała konflikt. Równoczesna archiwizacja firmy i tworzenie umowy zachowały spójny wynik pod wspólną blokadą gospodarstwa.
- Wymuszony błąd zapisu audytu wycofał utworzenie firmy, utworzenie umowy i konwersję; nie pozostało źródło `contract` bez szczegółów.

## Wyniki wydajności

| Operacja | P95, 1 klient | P95, 5 klientów | Błędy |
| --- | ---: | ---: | ---: |
| Lista firm | 7,15 ms | 39,96 ms | 0 |
| Lista umów | 15,47 ms | 71,18 ms | 0 |
| Utworzenie umowy | 33,53 ms | 157,19 ms | 0 |

Wynik dotyczy opisanej wielkości danych i pomiaru wewnątrz Django. Weryfikacja pełnej ścieżki HTTPS dla nowych ekranów może zostać wykonana po bolcie UI 011.

## Pokrycie zmienionych modułów

| Moduł | Pokrycie z gałęziami |
| --- | ---: |
| `family_income_services.py` | 92% |
| `family_income_views.py` | 98% |
| `models.py` | 100% |
| `record_serializers.py` | 100% |
| `record_services.py` | 96% |
| **Łącznie** | **97%** |

Pomiar nie obejmował migracji ani plików testowych; migrację zweryfikowano osobnym testem starego schematu. Pokrycie dotyczy zmienionych modułów, nie całego backendu.

## Problemy i ograniczenia

- Pierwsza próba nowego testu porównywała obiekt UUID z jego tekstową reprezentacją. Poprawiono wyłącznie asercję testu; ponowny przebieg przeszedł.
- Początkowo wygenerowana migracja nie spełniała formatowania projektu. Zastąpiono ją ręcznie utrzymywaną, równoważną migracją; `makemigrations --check`, zastosowanie migracji i pełne testy przeszły.
- W końcowym przeglądzie dodano zaplanowany indeks `(household, kind)` źródeł. Ponowna kontrola migracji, 80 testów i `scripts/quality.ps1` przeszły po tej zmianie.
- Nie wykryto otwartych błędów naruszających kryteria czterech historii. Pomiar wydajności nie obejmuje pełnej ścieżki HTTP/HTTPS i nie stanowi prognozy dla innych komputerów ani większego obciążenia.

## Checkpoint

Wszystkie wymagane kryteria bolta 010 zostały sprawdzone. Raport oczekuje na zatwierdzenie użytkownika przed formalnym zamknięciem bolta.

## Uzupełnienie po audycie z 26 września

Po zamknięciu bolta 010 audyt wykazał, że zwykła edycja umowy i innego źródła mogła nadpisać nowszą zmianę. Edycje wymagają teraz aktualnej wersji; konflikt zwraca `409` z kodem `source_conflict`. Sprawdzono też ochronę ostatniego aktywnego Ownera i logowanie poprzedniej oraz nowej roli. Po tych poprawkach pełny zestaw Django przeszedł 83/83 testów na odrębnej bazie PostgreSQL, kontrola jakości i sprawdzenie zgodności migracji przeszły. Te wyniki zastępują wcześniejszą liczbę 80 testów jako aktualny stan repozytorium; pozostałe pomiary w raporcie opisują pierwotny przebieg bolta 010.
