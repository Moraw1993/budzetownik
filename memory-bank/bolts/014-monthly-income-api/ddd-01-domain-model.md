---
unit: 002-monthly-income-api
bolt: 014-monthly-income-api
stage: domain-model
status: complete
updated: '2026-10-07T11:31:16Z'
---

# Stage 1 — model domenowy rzeczywistych przychodów

> Akceptacja: użytkownik odpowiedział „1” — zaakceptował D1–D4 oraz proponowany kontrakt API. Te decyzje są bazą dla Stage 2; implementacja nadal wymaga przejścia kolejnych checkpointów.

## Kontekst i granica domeny

`IncomeSource` i `Contract` opisują słownik/warunki uzyskiwania dochodu. Nie są księgą pieniędzy faktycznie otrzymanych. Nowa encja `IncomeRecord` zapisuje pojedyncze zdarzenie wpływu i jest przypisana do jednego gospodarstwa, jednego miesiąca rozliczeniowego, jednego odbiorcy oraz jednego elementu słownika. Data otrzymania opisuje, kiedy pieniądze wpłynęły; miesiąc rozliczeniowy opisuje, do którego okresu użytkownik przypisał wpływ.

Załączniki pozostają poza tym modelem i należą do bolta 015. Nie powstają tu budżety, wydatki, salda, wyliczenia netto ani konwersje walut.

## Język dziedzinowy

| Termin | Znaczenie |
| --- | --- |
| Rzeczywisty przychód (`IncomeRecord`) | Jeden zapis faktycznie otrzymanych pieniędzy. Nie jest umową ani kwotą sugerowaną przez słownik. |
| Okres rozliczeniowy (`AccountingMonth`) | Miesiąc, do którego użytkownik przypisuje przychód; niezależny od daty otrzymania. |
| Odbiorca | Aktywny członek gospodarstwa albo całe gospodarstwo (`member_id = null`). |
| Źródło (`IncomeSource`) | Zatwierdzona pozycja słownika przypisana dokładnie temu samemu odbiorcy. Wolny tekst nie jest dozwolony. |
| Snapshot historyczny | Wartości nazwy/tożsamości odbiorcy i źródła utrwalone przy zapisie, tak by późniejsza zmiana słownika nie przepisywała historii. |
| Aktywny / nieaktywny / zamknięty okres | Stan zdefiniowany przez bolt 013; wyłącznie `active` przyjmuje nowe i zmienione przychody. Odczyt historii pozostaje dostępny po zamknięciu. |

## Bounded context i agregaty

Kontekst `Monthly Income` należy do gospodarstwa i współdziała z kontekstami `Household`, `Accounting Periods` oraz istniejącym słownikiem `Family Income`. `IncomeRecord` jest korzeniem agregatu własnego wpisu. Agregat ma zachować spójność tenantową i nie może sam zmienić stanu miesiąca ani wpisu słownikowego.

Każda mutacja wpisu używa wspólnego protokołu transakcyjnego ADR-006: `Household → AccountingYear`, a następnie sprawdza aktualny stan miesiąca, dostęp, odbiorcę, źródło i wersję. Wpis i niezmienny `AuditLog` zapisują się atomowo (ADR-004). Zapytania list i sum są tenant-scoped; usunięte wpisy nie wchodzą do zwykłych list ani sum.

## Proponowane encje i obiekty wartości

### `IncomeRecord` (nowa encja)

Tożsamość: UUID. Proponowane dane bieżące:

- `household_id` — gospodarstwo właścicielskie;
- `accounting_month_id` — przypisany miesiąc; niemutowalny w v1;
- `member_id` — aktywny odbiorca będący członkiem gospodarstwa albo `null` dla gospodarstwa;
- `income_source_id` — dokładnie jeden istniejący element słownika;
- `amount` — kwota `Decimal(18,2)`, zapisana i transportowana jako tekst dziesiętny;
- `currency` — trzy wielkie litery, według aktualnej konwencji projektu; bez przewalutowania;
- `receipt_date` — rzeczywista data otrzymania, która może wypadać poza miesiącem/rokiem rozliczeniowym;
- snapshot odbiorcy i źródła (pola proponowane niżej);
- `version` — dodatnia wersja optymistyczna, zwiększana przy każdej skutecznej zmianie;
- pola utworzenia/aktualizacji oraz soft-delete: czas i wykonawca usunięcia.

Klucze obce do gospodarstwa, okresu, osoby i źródła nie mogą być kaskadowo usuwane. Obcy tenant albo zasób nieistniejący jest niewidoczny przez to API (404). Po usunięciu wpis nie jest zwracany ze standardowych list, odczytów ani sum; audit pozostaje.

### Snapshoty (propozycja D1)

Przy utworzeniu zapisać niezmienne wartości prezentacyjne: odbiorcę (`recipient_id`, nazwę w chwili zapisu, typ: osoba/gospodarstwo) oraz źródło (`source_id`, nazwę, typ i wersję). Dla źródła typu umowa zapisać także potrzebne historyczne dane umowy: identyfikator/nazwę firmy, typ umowy i nazwę typu własnego, jeśli dotyczy. Nie kopiować `Contract.gross_amount` ani `IncomeSource.default_monthly_amount` do `amount`.

Zmiana kwoty, waluty lub daty zachowuje snapshot. Jawna zmiana odbiorcy albo źródła waliduje nowe powiązanie i odświeża tylko związany snapshot. Ponowne wysłanie niezmienionego `member_id` lub `source_id` nie oznacza zmiany relacji. Aktualne wyświetlenie historii ma korzystać ze snapshotu, nie z bieżącej nazwy słownikowej. Historia zmian pozostaje w niezmiennym audycie; nie rekonstruujemy nieistniejącego pełnego rejestru wersji słownika.

### `IncomeSourceEligibility` (reguła/obiekt wartości)

To samo kryterium ma zasilać endpoint opcji źródeł i końcową walidację zapisu. Nowe przypisanie wymaga aktywnego źródła z tego samego gospodarstwa i dokładnie tego samego odbiorcy. Dla źródła/umowy obowiązuje inkluzywny overlap z miesiącem rozliczeniowym: `start_date <= month_end AND (end_date IS NULL OR end_date >= month_start)`. `receipt_date` nie wpływa na kwalifikację. Archiwalne osoby i źródła nie są dostępne dla nowego przypisania, również w dawnym aktywnym okresie; istniejące wpisy nadal są czytelne. Archiwizacja firmy sama nie unieważnia istniejącej aktywnej umowy. `one_off` nie ogranicza liczby osobnych wpływów.

Zmiana wyłącznie amount/currency/receipt_date zachowuje istniejące historyczne relacje bez ponownego odrzucenia ich z powodu późniejszej archiwizacji. Jeżeli użytkownik jawnie zmienia relację, nowa wartość musi przejść aktualną kwalifikację. Waluta wpisu jest niezależna od waluty źródła.

### `IncomeAmount`, `Currency`, `ReceiptDate` (proponowane ograniczenia)

- Amount: od `0.01` do `9999999999999999.99`; zero, wartości ujemne, nadmiar precyzji (>2 miejsc) i przekroczenie zakresu odrzucane bez zaokrąglania. Korekta przez edycję albo usunięcie istniejącego wpisu.
- Currency: dokładnie trzy wielkie litery, zgodnie z obecną walidacją. Nie obiecuje to pełnego katalogu ISO ani odmiennej precyzji walut.
- ReceiptDate: poprawna data kalendarzowa ISO; dozwolona poza miesiącem i rokiem rozliczeniowym, bez dodatkowego zakazu przyszłości.
- Żadne pole kwoty, okresu, właściciela, aktora audytu ani wersji nie może być przyjmowane poza jawnie opisanym kontraktem. Nieznane pola są odrzucane.

### `IncomeCreateIdempotency` (proponowana infrastruktura D4)

Przechowuje UUID klucza, gospodarstwo, aktora, typ operacji, fingerprint payloadu i referencję/wynik utworzenia. Zapis razem z `IncomeRecord` i audytem jest transakcyjny. Zakres klucza: household + actor + operation. Wymagany unikalny constraint bazy dla równoległych retry. Ten sam klucz i payload zwraca ten sam wynik bez drugiego wpisu i audytu; ten sam klucz z innym payloadem daje 409 `idempotency_conflict`. Nie deduplikujemy zwykłych podobnych wpływów po kwocie, dacie ani źródle. Dostęp sprawdzamy ponownie przed odpowiedzią z replay. Klucz zachowujemy co najmniej tak długo jak sam wpis.

## Operacje i niezmienniki

| Operacja | Reguła domenowa |
| --- | --- |
| Utworzenie | Miesiąc `active`; aktywny odbiorca i kwalifikujące się źródło; dodatnia kwota; zapis wpisu, snapshotów i audytu w jednej transakcji. Wymagany klucz idempotencji. |
| Odczyt/lista | Dostęp tylko w obrębie gospodarstwa; historia pokazuje snapshoty. Zwykła lista nie pokazuje usuniętych wpisów. |
| Edycja | Miesiąc `active`; wymagany `expected_version`; `month_id` niezmienny. Zmiana zwiększa wersję i zapisuje audyt before/after. Tylko jawna zmiana odbiorcy/źródła odświeża snapshot. |
| Usunięcie | Miesiąc `active`; soft-delete z `expected_version`, czasem i wykonawcą; wersja rośnie, audit pozostaje, rekord znika ze standardowych odczytów i sum. |
| Sumy okresu/roku | Agregują tylko nieusunięte rzeczywiste wpisy po przypisanym miesiącu, osobno dla każdej waluty; bez konwersji i bez kwot kontraktów. Czytelne również po zamknięciu okresu. |
| Opcje źródeł | Dla wybranego okresu i odbiorcy zwracają pozycje spełniające ten sam predykat, który obowiązuje przy zapisie. Szybkie dodanie pozostaje operacją słownika i samo nie zapisuje wpływu. |

## Repozytoria, usługi i zdarzenia

Proponowane interfejsy repozytoriów: `IncomeRecordRepository` (scoped read/list/create/update/soft-delete/aggregate) i `IncomeCreateIdempotencyRepository` (lookup/atomic reserve/store result). To propozycja granic, nie obowiązek dodania klas abstrakcyjnych: implementacja Django może używać istniejącego wzorca serwisów i ORM bez sztucznej warstwy.

Proponowane przypadki użycia: `CreateIncomeRecord`, `UpdateIncomeRecord`, `DeleteIncomeRecord`, `ListIncomeRecords`, `ListEligibleIncomeSources`, `GetPeriodIncomeTotals`, `GetYearIncomeTotals`. Kwalifikacja źródeł należy do współdzielonej domenowej funkcji/reguły, nie do kopii w view i serializerze.

Audit jest niezmiennym rekordem operacji, nie event store. `income_record.created`, `.updated`, `.deleted` to proponowane action names; before/after powinny zawierać wyłącznie zdefiniowane pola biznesowe/snapshoty i nie zawierać bajtów załączników. Załączniki i ich metadane należą do 015.

## Granica kontraktu HTTP proponowana do zatwierdzenia

Wszystkie poniższe trasy są pod `/api/households/{household_id}/` i kończą się ukośnikiem:

| Trasa | Operacje i zachowanie |
| --- | --- |
| `accounting-years/{year_id}/months/{month_id}/incomes/` | GET paginowany; POST tworzy. |
| `accounting-years/{year_id}/months/{month_id}/incomes/{income_id}/` | GET/PATCH/DELETE. PATCH/DELETE wymagają wersji; DELETE miękki. |
| `accounting-years/{year_id}/months/{month_id}/income-source-options/?member_id={UUID}` | GET źródeł dla osoby; pominięte `member_id` oznacza źródła gospodarstwa. |
| `accounting-years/{year_id}/months/{month_id}/income-totals/` | GET sum miesiąca wg waluty. |
| `accounting-years/{year_id}/income-totals/` | GET sum roku przypisanego wg miesięcy, a nie daty wpływu. |

Proponowany POST:

```http
Idempotency-Key: 98d3e9df-c0c5-4a7c-8c90-9f125af6b3ab
```

```json
{
  "member_id": null,
  "source_id": "7b372ef3-262e-46cf-b9c7-4c7bb302bc32",
  "amount": "800.00",
  "currency": "PLN",
  "receipt_date": "2026-09-30"
}
```

`member_id: null` oznacza cały household. Proponowana odpowiedź rekordu zawiera `id`, `household_id`, `month_id`, `member_id`, `source_id`, `amount`, `currency`, `receipt_date`, `version`, `recipient_snapshot`, `source_snapshot`, `created_at`, `updated_at`. Kwoty request/response są stringami dziesiętnymi. PATCH akceptuje tylko `amount`, `currency`, `receipt_date`, `member_id`, `source_id` oraz obowiązkowe `expected_version`; `month_id` jest niemutowalny. DELETE body przenosi `expected_version`.

Listy używają bieżącej paginacji projektu: `count`, `next`, `previous`, `results`, 50 rekordów. Kolejność wpisów: `receipt_date`, `created_at`, `id`; kolejność opcji źródeł: `name`, `id`. Sumy mają kształt `{"totals":[{"currency":"PLN","amount":"1000.00"}]}`; brak wyników daje `{"totals":[]}`. Waluty w odpowiedzi uporządkowane alfabetycznie. Suma agregatowa może przekroczyć zakres pojedynczego pola `Decimal(18,2)`.

Proponowana semantyka błędów: 400 dla kształtu, nieznanych pól, kwot/dat i kwalifikacji; 403 dla braku zapisu/CSRF; 404 dla obcego lub brakującego zasobu; 409 dla nieaktywnego/zamkniętego okresu, niezgodnej wersji albo konfliktu idempotencji. Kody maszynowe i wspólną kopertę błędu trzeba potwierdzić w Stage 2 po porównaniu z istniejącym API.

## Zmiany stories proponowane po checkpointcie

- Story `001-record-income`: doprecyzować idempotency key, snapshots, soft-delete, wersjonowanie edit/delete, relację do okresu i brak podwójnego audytu przy retry.
- Story `002-select-dictionary-source`: wpisać regułę odbiorcy, aktywności i inkluzywnego overlap oraz zachowanie dla archiwizacji.
- Story `003-record-amount-currency-date`: wpisać precyzyjny zakres kwot i brak silent rounding; potwierdzić przyszłe daty dozwolone.
- Story `004-period-totals-by-currency`: określić pusty wynik jako `totals: []` oraz agregację po przypisanym miesiącu.
- Nie dodawać osobnej story o załącznikach tutaj: istniejąca story `005-private-income-attachments` przypisana jest do bolta 015. Edycję/usuwanie i retry dopisać do 001, aby uniknąć konfliktu numeracji.
- D5 (załączniki) i D6 (UI) nie są częścią tego checkpointu.

## Zatwierdzone decyzje i granice

Użytkownik zaakceptował wszystkie propozycje D1–D4 oraz kontrakt API z poprzednich sekcji. Przyjęte są zatem: osobny wpis z historycznymi snapshotami i soft-delete; kwalifikacja źródła względem odbiorcy i miesiąca; dodatnia kwota `Decimal(18,2)` bez zaokrągleń i data niezależna od okresu; niemutowalny miesiąc, wersjonowane PATCH/DELETE i idempotentny POST z UUID `Idempotency-Key`; oraz przedstawione trasy, kształty odpowiedzi, paginacja i semantyka statusów.

Osobna decyzja dotycząca ochrony przed opóźnionym żądaniem lifecycle po cyklu close→reopen z 013 nie była częścią tego checkpointu. Bolt 014 korzysta z bieżącego zaakceptowanego kontraktu 013; ewentualna zmiana tego kontraktu wymaga osobnego checkpointu.
