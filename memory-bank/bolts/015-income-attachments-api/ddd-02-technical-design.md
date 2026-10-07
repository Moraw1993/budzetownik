---
unit: 002-monthly-income-api
bolt: 015-income-attachments-api
stage: design
status: awaiting-review
updated: '2026-10-07T20:18:58Z'
---

# Stage 2 — projekt techniczny prywatnych załączników przychodu

## Zakres i zaakceptowane wejścia

Projekt realizuje zaakceptowany model z [ddd-01-domain-model.md](ddd-01-domain-model.md): IncomeRecord pozostaje jedynym korzeniem agregatu, mutacje wymagają aktywnego miesiąca, odczyt pozostaje możliwy w dowolnym stanie okresu, a cała partia metadanych i jej audyt są widoczne atomowo.

Bolt 015 dodaje metadane, prywatny storage, upload wieloplikowy, listę, autoryzowany download, logiczne usunięcie oraz reconciliation. Nie zmienia reguł kwoty i źródła z bolta 014, nie dodaje UI ani zewnętrznych usług. Obowiązują istniejące: Django/DRF, PostgreSQL, sesje/CSRF, locked_access, immutable AuditLog i trwały wolumen media_data.

## Architektura

Przepływ HTTP: DRF route/view → strict multipart serializer i polityka dostępu → use-case uploadu → prywatny staging i finalizacja filesystemu → krótka transakcja Household → AccountingYear → IncomeRecord → metadane i AuditLog. Pobranie zwraca autoryzowany strumień FileResponse.

View mapuje HTTP, serializer waliduje wejście, serwis stosuje reguły domenowe/transakcyjne, model zapisuje metadane, a wąski adapter filesystemu ukrywa ścieżki. Nie dodawać ogólnego frameworka storage, sygnałów Django ani publicznego MEDIA_URL.

## Kontrakt API

Wszystkie trasy są pod /api/households/{household_id}/accounting-years/{year_id}/months/{month_id}/incomes/{income_id}/. POST nie wymaga klucza idempotencji; po utracie odpowiedzi klient najpierw pobiera listę i sprawdza, czy załączniki już istnieją, zanim ponowi wysyłkę. Każdy identyfikator jest rozwiązywany w zakresie gospodarstwa, roku, miesiąca i wpisu. Brak, obcy tenant, usunięty wpis albo nieaktywny załącznik dają ten sam 404.

| Metoda i trasa | Dostęp | Kontrakt |
| --- | --- | --- |
| GET .../attachments/ | Każdy członek z read access | 200 z results aktywnych załączników, kolejność created_at,id; najwyżej 20. |
| POST .../attachments/ | Owner/Administrator, aktywny miesiąc | multipart/form-data, powtarzane pole files, 1–5 plików; 201 z results. |
| GET .../attachments/{attachment_id}/download/ | Każdy członek z read access | Autoryzowany wymuszony download aktywnego pliku. |
| DELETE .../attachments/{attachment_id}/ | Owner/Administrator, aktywny miesiąc | 204 po logicznym odebraniu dostępu i atomowym zapisie business audit. |

Odpowiedź metadanych zawiera tylko id, bezpieczną nazwę name, rozpoznany media_type, size_bytes i created_at. Nie zwraca storage_key, ścieżki, URL-a, skrótu ani stanu cleanup. Opis nie należy do MVP, bo nie jest wymagany przez story ani obecny formularz. Multipart akceptuje tylko pole files; obce pola, pusty upload, JSON i URL-e są odrzucane.

## Limity i walidacja

| Ograniczenie | Limit MVP |
| --- | --- |
| Pojedynczy plik | 10 MiB |
| Cała partia | 25 MiB |
| Pliki na żądanie | 1–5 |
| Aktywne pliki na IncomeRecord | Maksymalnie 20 |
| Aktywna suma na IncomeRecord | Maksymalnie 50 MiB |
| Nazwa display | Maksymalnie 255 znaków po normalizacji |

Aplikacja liczy rzeczywiste bajty podczas strumieniowego zapisu. Content-Length, MIME i rozszerzenie klienta są niezaufane. Przekroczenie limitu pola/partii/rekordu zwraca walidacyjny 400; limit request body Caddy wynosi 26 MiB i daje 413. Django multipart temp files trafiają wyłącznie do prywatnego MEDIA_ROOT/.incoming, a nie do ogólnego /tmp. Caddy request_body jest dostępne od 2.10.0 i oznaczone jako experimental; implementacja ustawi obraz co najmniej na caddy:2.10-alpine i sprawdzi konfigurację poleceniem caddy validate. Dokumentacja: https://caddyserver.com/docs/caddyfile/directives/request_body. Aplikacja niezależnie egzekwuje per-file i łączny limit również wtedy, gdy request przejdzie inną ścieżką.

Serwer rozpoznaje PNG, JPEG i PDF po sygnaturze oraz podstawowej walidacji strukturalnej. Wynik zapisuje jako kanoniczne image/png, image/jpeg albo application/pdf; sprzeczna nazwa rozszerzenia, pusta lub uszkodzona zawartość jest odrzucana. Projekt nie wprowadza nieobecnej biblioteki ani usługi skanowania. Lokalne malware scanning nie jest obecnie dostępne, więc pliki są niezaufane i nigdy nie są serwowane inline: download wymusza Content-Disposition attachment oraz X-Content-Type-Options: nosniff.

Nazwa pliku jest Unicode-normalizowana, oczyszczona z separatorów, znaków sterujących i ścieżek; pusta po normalizacji jest odrzucana. Klucz storage jest losowym UUID, nigdy nazwą użytkownika. SHA-256 liczony podczas zapisu kontroluje integralność obiektu; nie jest dowodem autentyczności i nie trafia do odpowiedzi ani audytu.

## Model danych

Dodaj IncomeAttachment jako child IncomeRecord z FK PROTECT do household, income record i aktorów. Gospodarstwo, miesiąc rodzica i wpis są zgodne z URL i niezmienne po utworzeniu.

| Pole | Kontrakt |
| --- | --- |
| id | UUID PK. |
| household, income_record | Właścicielstwo i parent bez możliwości przepięcia. |
| original_name | CharField(255), bezpieczna nazwa display. |
| media_type | Wyłącznie kanoniczne MIME PNG/JPEG/PDF. |
| size_bytes | Rzeczywisty dodatni rozmiar do 10 MiB. |
| storage_key | Unikalny klucz względny i losowy; nigdy w API/audycie. |
| content_sha256 | 64 małe znaki hex. |
| availability_state | Jawne available albo removed; niezależne od kwarantanny. |
| created_at, created_by | Czas i aktor utworzenia. |
| removed_at, removed_by | Null razem dla available; wymagane dla removed. |
| storage_deleted_at | Null dla pliku dostępnego lub oczekującego sprzątania; ustawiany po potwierdzonym fizycznym usunięciu. |

Constraints parują availability_state z removed_at/by. Indeksy: household + income_record + state + created_at + id oraz storage_deleted_at do kolejki cleanup. Nie dodawać FileField ani public URL.

AuditLog używa object_type income_attachment i akcji created/deleted. Snapshot zawiera household, income, attachment ID, bezpieczną nazwę, typ, rozmiar i stan logiczny. Nie zawiera bajtów, SHA, storage_key ani ścieżki. Rekord metadata i jego audit są zapisywane w tej samej transakcji DB.

## Prywatny storage i upload

Wolumen media_data przetrwa restart i jest uwzględniony w obecnej procedurze kopii/odtworzenia. Caddy kieruje tylko /api/* do backendu; żaden serwer statyczny nie wystawia media. Obiekty trafiają do MEDIA_ROOT/income-attachments/{household_uuid}/{random_attachment_uuid}; staging i multipartowe pliki tymczasowe do MEDIA_ROOT/.incoming.

1. Uwierzytelnij sesję/CSRF, sprawdź household i Owner/Administrator, potem waliduj multipart.
2. Zapisuj strumieniowo do prywatnego stagingu z manifestem batch ID, timestampem i odświeżanym heartbeat. W trakcie kopiowania egzekwuj limity, waliduj nazwę/typ/strukturę i oblicz SHA-256. Jeden błędny plik odrzuca całą partię.
3. Po walidacji wszystkich plików przenieś je do finalnych losowych kluczy na tym samym wolumenie. Flush i fsync plików oraz katalogu docelowego potwierdzają trwałość; całe filesystem I/O kończy się przed transakcją, a bajty muszą być pobieralne, zanim metadata stanie się widoczna.
4. Otwórz krótką transakcję: locked_access blokuje Household i ponownie sprawdza rolę; zablokuj AccountingYear przez select_for_update; sprawdź active state; zablokuj IncomeRecord. Zweryfikuj household/month, deleted_at IS NULL i bieżące limity liczby/rozmiaru po równoległych uploadach.
5. Utwórz wszystkie wiersze IncomeAttachment i audyty w jednej transakcji. Commit ujawnia całą partię atomowo. Zamknięcie miesiąca, usunięcie rodzica i upload używają tej samej kolejności blokad Household → AccountingYear → IncomeRecord.
6. Przy każdym błędzie nie publikuj metadata i sprzątnij staging/promowane obiekty best-effort. Awaria kompensacji pozostawia niedostępne bajty do kontrolowanego reconciliation.

Nie wykonuj długiego I/O, walidacji, rename ani kasowania pod blokadami DB. Kolejność Household → AccountingYear odpowiada zaakceptowanemu [ADR-006](../013-periods-api/adr-006-accounting-year-lock-for-financial-writes.md). Proces reconciliation nie usuwa aktywnego staging claim z heartbeat. Obiekt finalny bez właściciela po crashu przed commit można usunąć dopiero po 24-godzinnym grace period.

## Odczyt, usunięcie i retencja

List/download wymaga aktualnej roli read oraz household/year/month/income scope; działa również przy inactive/closed miesiącu. Download dodatkowo wymaga nieusuniętego rodzica i available attachment. Zwracaj kanoniczny MIME, FileResponse jako attachment, bezpieczną nazwę RFC 5987, nosniff i Cache-Control: private, no-store. Nie przekierowuj do storage.

DELETE załącznika wymaga active month. Pod lockami ustaw availability_state=removed, removed_at/by oraz zapisz audit w tej samej krótkiej transakcji. Po commit callback wykonuje idempotentne usunięcie, po czym w osobnej krótkiej transakcji ustawia storage_deleted_at. Awaria pozostawia plik logicznie niedostępny i oczekujący; sprzątanie może działać także po zamknięciu okresu.

Soft-delete IncomeRecord przez istniejący use case 014 w tej samej transakcji logicznie usuwa jego dostępne załączniki i zapisuje audyty; po commit zleca usunięcie bajtów. Pliki nie są zachowywane po usunięciu przychodu, ale historyczne metadata i audyt pozostają. Hard purge jest poza zakresem. Backup media może zachować usunięte bajty do rotacji kopii.

Management command reconcile_income_attachment_storage jest idempotentny i ma dry-run. Oznacza completed rekordy removed po potwierdzonym/idempotentnym usunięciu; usuwa stale staging i finalne obiekty bez aktywnego/oczekującego właściciela dopiero po 24 h; nigdy nie usuwa aktywnego claim, available object ani pliku objętego cleanup. Brak bajtów pod aktywnym metadata jest błędem integralności, a nie zwykłym orphanem. Command działa porcjami i bez dodatkowego kontenera; powinien być cyklicznie uruchamiany przez operatora.

## Błędy HTTP i bezpieczeństwo

- 400: błędne pola/formularz, puste lub nadmierne pliki, nieobsługiwany/uszkodzony format, przekroczone limity lub obce pola.
- 403: rola Member/Viewer próbuje mutacji albo CSRF nie przechodzi.
- 404: obcy/brakujący household, year, month, income lub attachment; soft-delete parenta albo logiczne usunięcie attachment.
- 409 income_period_not_active: upload/delete przy inactive/closed month, po końcowym sprawdzeniu pod blokadą roku.
- 413: body większe niż limit reverse proxy; klient obsługuje kod bez zależności od Caddy response envelope.
- 405: metoda poza kontraktem.
- Błąd storage albo audytu nie zwraca sukcesu. Audit i metadata wycofują się razem; prywatne bajty są kompensowane albo zostawione do reconciliation.
- Odrzucony upload nie tworzy successful business audit. Log bezpieczeństwa może zawierać household/user/request ID i kod przyczyny, ale bez nazw, MIME klienta, ścieżek i bajtów.

## Strategia testów

1. Multipart PNG/JPG/JPEG/PDF tworzy powiązane child metadata, kanoniczny MIME i poprawny SHA.
2. Typ nieobsługiwany, fałszywe MIME/rozszerzenie, puste/uszkodzone sygnatury, path traversal oraz każda granica limitów; jedna porażka nie pozostawia metadata ani final bytes.
3. Role, tenant isolation, dostęp przez obce income/month, parent soft-delete i usunięty attachment; lista/download w inactive/closed, write odmówione.
4. PostgreSQL race close kontra końcowy upload, upload kontra income delete i równoległe uploady ograniczeń. Rzeczywiste filesystem I/O nie może zachodzić w transakcji.
5. Wymuszone audit failure wycofuje całą partię; awaria po promotion kompensuje pliki lub zostawia cleanup claim; nie ma części widocznych rows.
6. Delete rodzica logicznie odbiera dostęp do wszystkich plików i audytuje; cleanup retry nie przywraca dostępu.
7. Reconciliation dry-run/execution chroni aktywny heartbeat, retained/pending cleanup, rozpoznaje brakujące bajty, usuwa orphan dopiero po grace period; restart i odtworzenie media_data.
8. Migration check, focused Django tests, PostgreSQL concurrency tests, Ruff i scripts/quality.ps1. Przed zamknięciem Stage 5 także pełny zestaw testów oraz sprawdzenie zmienionych plików.

## Kolejność implementacji

1. Model, constraints, indeksy, migracja, prywatny adapter storage i testy jego ograniczeń.
2. Konfiguracja limitów/temp dir/Caddy body cap oraz strict multipart serializer i schema odpowiedzi.
3. Endpoint uploadu z walidacją/staging/finalizacją i atomowym metadata+audit.
4. Lista, download, logiczne delete i integracja soft-delete IncomeRecord z lifecycle załączników.
5. Idempotentny management command reconciliation, testy API/storage/race/failure i weryfikacja quality.

## Zgodność ze story 005

Każdy zaakceptowany plik ma jednego rodzica i household; wieloplikowa partia nie tworzy częściowo widocznych metadata; limity i typy są wyraźne; storage jest prywatny i trwały; download wymaga aktualnej autoryzacji; tenant/rola/okres sprawdzane są ponownie przy finalnym zapisie; cleanup nie przywraca dostępu i nie usuwa aktywnych claims.
