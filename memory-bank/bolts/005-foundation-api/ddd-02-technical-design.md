---
unit: 002-foundation-api
bolt: 005-foundation-api
stage: design
status: complete
updated: 2026-09-11T19:56:36+02:00
---

# Technical Design - Foundation API: members, income and audit

## Architecture Pattern

Rozszerzenie modularnego monolitu Django w aplikacji `households`, zgodne z
boltami 003–004: modele oraz ograniczenia danych, selektory odczytu,
transakcyjne usługi przypadków użycia, serializatory DRF i cienkie widoki.
Nie wprowadzamy osobnego mikroserwisu ani abstrakcyjnego repozytorium.

Zapisy w obrębie gospodarstwa stosują ADR-002: blokują `Household`, a następnie
ponownie odczytują rolę wykonawcy. Tworzenie wpisu audytu należy do tej samej
transakcji co zmiana źródła dochodu.

## Layer Structure

```text
HTTP request
    │
    ├─ views.py          ─ uwierzytelnienie, CSRF, odpowiedź HTTP
    ├─ serializers.py    ─ walidacja danych wejściowych i reprezentacja
    ├─ services.py       ─ autoryzacja po blokadzie i transakcje przypadków użycia
    ├─ selectors.py      ─ filtrowane odczyty w granicy gospodarstwa
    └─ models.py         ─ encje, indeksy i ograniczenia bazy PostgreSQL
```

## API Design

Wszystkie adresy wymagają sesji; `POST`, `PATCH` i `DELETE` wymagają CSRF.
Brak dostępu do gospodarstwa i nieistniejący zasób zwracają `404`; Member i
Viewer w dostępnym gospodarstwie otrzymują `403` dla modyfikacji.

| Endpoint | Method | Request | Response |
| --- | --- | --- | --- |
| `/api/households/{household_id}/members/` | GET | — | lista członków gospodarstwa; wszystkie role tylko odczyt. |
| `/api/households/{household_id}/members/` | POST | nazwa, opcjonalne `account_id`, opcjonalne `relation_type_id` | `201` z członkiem; tylko Owner/Administrator. |
| `/api/households/{household_id}/members/{member_id}/` | PATCH | edytowalne dane, opcjonalne powiązanie konta/relacji | `200`; tylko Owner/Administrator. |
| `/api/households/{household_id}/members/{member_id}/deactivate/` | POST | — | `200` z nieaktywnym członkiem; tylko Owner/Administrator. |
| `/api/households/{household_id}/relation-types/` | GET, POST | dla POST: `name` | lista lub `201`; zapis tylko Owner/Administrator. |
| `/api/households/{household_id}/relation-types/{id}/` | PATCH | `name` | `200`; tylko Owner/Administrator. |
| `/api/households/{household_id}/relation-types/{id}/deactivate/` | POST | — | `200`; nie usuwa członków. |
| `/api/households/{household_id}/income-sources/` | GET, POST | dla POST: pola FR-08 oraz opcjonalny `member_id` | lista lub `201`; zapis tylko Owner/Administrator. |
| `/api/households/{household_id}/income-sources/{id}/` | GET, PATCH | dla PATCH: edytowalne pola FR-08 | `200`; zapis tylko Owner/Administrator. |
| `/api/households/{household_id}/income-sources/{id}/deactivate/` | POST | — | `200`; tworzy audyt; tylko Owner/Administrator. |
| `/api/households/{household_id}/audit-logs/` | GET | opcjonalne filtry obiektu/czasu | lista tylko do odczytu dla Ownera. |

Klient nie przekazuje `household_id` w treści, wykonawcy audytu, stanu audytu
ani flagi aktywności bez dedykowanego przypadku użycia. Pola `account_id`,
`member_id` i `relation_type_id` są zawsze weryfikowane w tym samym
`household_id` z URL.

## Data Persistence

| Table | Columns | Relationships |
| --- | --- | --- |
| `households_householdmember` | UUID, household FK, account FK nullable, display fields, relation type FK nullable, `is_active`, `deactivated_at`, timestamps | household CASCADE; account PROTECT; relacja tylko z tego samego gospodarstwa walidowana usługą; unikalność `(household, account)` dla niepustego konta. |
| `households_relationtype` | UUID, household FK, name, `is_active`, `deactivated_at`, timestamps | household CASCADE; unikalna aktywna nazwa w gospodarstwie. |
| `households_incomesource` | UUID, household FK, member FK nullable, pola FR-08, `Decimal` amount, currency, `is_active`, `deactivated_at`, timestamps | household CASCADE; member PROTECT; zgodność gospodarstwa walidowana usługą. |
| `households_auditlog` | UUID, household FK, actor FK nullable, action, object type/id, occurred at, JSON before/after | household PROTECT, actor SET NULL/PROTECT zgodnie z istniejącą polityką kont; indeksy dla gospodarstwa i czasu oraz obiektu. |

Migracja Django dodaje modele, ograniczenia, indeksy i wartości wyboru
częstotliwości/kategorii. Kwota korzysta z `DecimalField`; waluta ma trzy znaki
alfabetyczne. Publiczne API nie oferuje trwałego `DELETE` dla tych encji.

## Security Design

| Concern | Approach |
| --- | --- |
| Authentication | Sesja Django według ADR-001. |
| Authorization | Wspólna polityka z ADR-002; aktualna rola z bazy po blokadzie gospodarstwa. |
| Tenant isolation | Selektory filtrują po gospodarstwie i członkostwie; szczegóły pobierane po `(household_id, resource_id)`. |
| Integrity | `transaction.atomic()` obejmuje zmianę źródła i zapis audytu; ograniczenia bazy chronią przed podwójnym przypisaniem konta. |
| Audit privacy | Snapshot jest budowany z whitelisty pól; hasła, cookies i tokeny są odrzucane przed trwałym zapisem. |

## NFR Implementation

| Requirement | Design Approach |
| --- | --- |
| P95 < 500 ms dla podstawowego API | Indeksy po `household_id`, aktywności i czasie; listy paginowane; brak zewnętrznych wywołań. Pomiar należy do odbioru lokalnego w bolcie 008. |
| Data integrity | Django migrations, `DecimalField`, ograniczenia spójności, transakcje dla wieloobiektowych zmian. |
| History preservation | Logiczna dezaktywacja zamiast usuwania oraz niezależny, niemodyfikowalny audyt. |

## Error Handling

| Error Type | Code | Response |
| --- | --- | --- |
| Brak sesji/CSRF | 401/403 | standardowa odpowiedź uwierzytelnienia lub CSRF, bez danych gospodarstwa. |
| Brak zasobu lub dostępu do gospodarstwa | 404 | jednolity błąd bez potwierdzania istnienia obcego zasobu. |
| Zbyt niska rola | 403 | komunikat o wymaganej roli bez ujawniania danych obcego gospodarstwa. |
| Niezgodne powiązanie konta, członka lub relacji | 400 | błąd pola wskazujący niespójność zakresu gospodarstwa. |
| Naruszona unikalność przypisania konta | 400 | błąd walidacji; brak częściowego zapisu. |
| Niedozwolona operacja destrukcyjna | 405 | publiczny kontrakt nie udostępnia trwałego usuwania. |

## External Dependencies

Brak nowych zależności zewnętrznych. Implementacja użyje istniejących Django,
Django REST Framework i PostgreSQL; nie wysyła e-maili ani nie tworzy
zewnętrznych transakcji finansowych.

## Doprecyzowanie kontraktu po implementacji — 2026-09-18T08:07:00+02:00

- Kod operacji został wydzielony do `record_services.py`, `record_serializers.py`
  i `record_views.py` w istniejącej aplikacji `households`. Wspólna obsługa trzech
  rodzajów rekordów eliminuje powielanie walidacji i cyklu zapisu.
- Pole nazwy członka to `display_name` (180 znaków), nazwa relacji `name`
  (100 znaków). `account_id` jest liczbą całkowitą, pozostałe identyfikatory UUID.
- Dochód: `name`, `category`, `payer`, `start_date`, `end_date`,
  `default_monthly_amount`, `currency`, `frequency`, `is_regular`, `description`,
  opcjonalny `member_id`. Brak członka oznacza źródło gospodarstwa.
- `category` jest edytowalnym tekstem (100 znaków), bez narzucania nazw świadczeń.
  Częstotliwości: `monthly`, `weekly`, `quarterly`, `yearly`, `one_off`, `irregular`.
  Kwota jest nieujemna, ma do 18 cyfr, w tym 2 po przecinku; JSON zwraca ją jako tekst.
- Listy zwracają `{count, next, previous, results}`, 50 elementów na stronę,
  parametr `page`. Zwracane są również rekordy archiwalne, rozróżnione przez
  `is_active` i `deactivated_at`. GET szczegółów dostępny dla wszystkich trzech zasobów.
- Filtry audytu: `object_id`, `object_type=income_source`, `since`, `until`
  (daty ISO 8601); odczyt tylko dla Ownera.
- Ponowna dezaktywacja jest idempotentna, bez dodatkowego audytu.
  Edycja archiwalnego obiektu jest odrzucana; reaktywacja nie jest częścią tego API.
  Istniejące odwołania do archiwalnych członków/relacji pozostają zachowane,
  nowe przypisania wymagają aktywnego obiektu w tym samym gospodarstwie.
- Klucze obce nowych rekordów i audytu korzystają z PROTECT, również dla
  gospodarstwa i wykonawcy. Chroni to historię przed przypadkową kaskadą ORM.
  Niezmienialność audytu jest gwarancją publicznego API, nie ochroną przed
  administratorem bazy lub bezpośrednią operacją ORM.
