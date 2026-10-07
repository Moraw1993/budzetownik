---
unit: 002-monthly-income-api
bolt: 015-income-attachments-api
stage: design
status: awaiting-review
updated: '2026-10-07T20:26:04Z'
---

# Stage 2 — projekt techniczny prywatnych załączników przychodu

## Zakres i zaakceptowane wejścia

Projekt realizuje zaakceptowany model z [ddd-01-domain-model.md](ddd-01-domain-model.md): IncomeRecord jest jedynym korzeniem agregatu; mutacje użytkownika wymagają aktywnego miesiąca i nieusuniętego rodzica; odczyt pozostaje dozwolony w każdym stanie okresu; widoczność metadata i business audit jest atomowa.

Bolt dodaje metadata, prywatny storage, upload wieloplikowy, listę, autoryzowany download, logiczne usunięcie i reconciliation. Nie zmienia reguł finansowych z 014 i nie dodaje UI ani usług zewnętrznych. Obowiązują Django/DRF, PostgreSQL, sesje/CSRF, locked_access, AuditLog i trwały wolumen media_data.

## Architektura

DRF view mapuje HTTP, strict serializer sprawdza wejście, custom upload handler od pierwszych bajtów zapisuje do claimowanego stagingu, use-case zatwierdza filesystem przed krótką transakcją Household → AccountingYear → IncomeRecord, a model zapisuje metadata. Download używa autoryzowanego FileResponse. Wąski adapter ukrywa ścieżki. Nie dodajemy generycznego storage frameworka, sygnałów Django ani publicznego MEDIA_URL.

## Kontrakt API

Wszystkie ścieżki są pod /api/households/{household_id}/accounting-years/{year_id}/months/{month_id}/incomes/{income_id}/. Identyfikatory zawsze rozwiązuje się w zakresie household/year/month/income.

| Metoda i trasa | Dostęp | Kontrakt |
| --- | --- | --- |
| GET .../attachments/ | Household read access | 200 z results aktywnych załączników, sortowanie created_at,id; maksymalnie 20. |
| POST .../attachments/ | Owner/Administrator, active month | multipart/form-data, powtarzane pole files, 1–5 plików; 201 z results. |
| GET .../attachments/{attachment_id}/download/ | Household read access | Autoryzowany download aktywnego pliku. |
| DELETE .../attachments/{attachment_id}/ | Owner/Administrator, active month | 204 po logicznym usunięciu i atomowym audycie. |

Metadata odpowiedzi zawierają tylko id, bezpieczną nazwę, media_type, size_bytes i created_at. Nie ujawniają storage_key, ścieżki, URL-a, SHA, batch ID ani stanu cleanup. Opis nie jest częścią MVP. Multipart akceptuje tylko files; obce pola i pusty upload są odrzucane.

POST jest jawnie nieidempotentny: nie wymaga Idempotency-Key i klient nie może automatycznie ponawiać uploadu po timeout/utracie odpowiedzi. Wynik takiego żądania jest nieznany; odświeżenie listy może pokazać nowe pozycje, ale nie dowodzi, która partia je utworzyła. Jawne ponowne wysłanie jest nową operacją i może utworzyć duplikaty.

Brak/obcy household, year, month, income lub attachment, usunięty parent i logical-removed attachment mapują się na 404. Przy mutacji istniejący, nieusunięty parent i attachment dla DELETE rozstrzyga się przed błędem inactive/closed month; po ich potwierdzeniu stan okresu daje 409 income_period_not_active.

## Limity i ochrona parsera

| Ograniczenie | Limit MVP |
| --- | --- |
| Pojedynczy plik | 10 MiB |
| Cała partia | 25 MiB |
| Pliki na żądanie | 1–5 |
| Multipart non-file fields | Tylko files, maksymalnie 1 pole |
| Aktywne załączniki na income | Maksymalnie 20 |
| Aktywna suma na income | Maksymalnie 50 MiB |
| Display name | Maksymalnie 255 znaków po normalizacji |
| Pamięć handlera | Maksymalnie jeden chunk 64 KiB plus ograniczony stan parsera |
| Czas żądania uploadu | Maksymalnie 10 min; Caddy idle/min-rate guard i monotoniczny deadline handlera |

Django DATA_UPLOAD_MAX_MEMORY_SIZE=1 MiB dotyczy danych formularza bez bajtów plików. Nie jest limitem plików ani ochroną przed ich zapisaniem do temp. Dlatego pierwsza granica musi działać przed parserem i CSRF:

1. AttachmentUploadLimitMiddleware jest umieszczony po AuthenticationMiddleware, ale przed CsrfViewMiddleware. W process_view dla dokładnej trasy POST najpierw odrzuca nieautoryzowaną sesję lub rolę bez dostępu do write; nie pozwala CSRF uruchomić parsera dla takiego żądania.
2. Dla uprawnionego requestu tworzy unikalny batch claim i OS advisory lock przed jakimkolwiek odczytem request.POST/request.FILES, a następnie instaluje jako jedyny FILE_UPLOAD_HANDLER ClaimedAttachmentUploadHandler. W ten sposób także CSRF, które parsuje request.POST, trafia już do ograniczonego handlera.
3. Handler zapisuje każdy multipart chunk bezpośrednio do pliku wewnątrz claim directory. Nie uruchamia MemoryFileUploadHandler ani TemporaryFileUploadHandler i nie tworzy kopii parsera w /tmp. Liczy rzeczywiste bajty per file i batch, liczbę plików i elapsed monotonic time przed zapisem kolejnego chunku. Brak/fałszywy Content-Length nie zmienia limitu.
4. Chunk wynosi najwyżej 64 KiB; przekroczenie per-file, total, file count, pola albo czasu przerywa upload natychmiast. Przy abort/CSRF failure/rozłączeniu request middleware zamyka partial files pod lockiem i usuwa claim; jeżeli cleanup zawiedzie, trwały claim zostaje do reconciliation.
5. Ustawienia Django DATA_UPLOAD_MAX_NUMBER_FIELDS=10 i DATA_UPLOAD_MAX_NUMBER_FILES=5 ograniczają liczbę pól/plików parsera. Django non-file fields nadal mają DATA_UPLOAD_MAX_MEMORY_SIZE; w attachment payload nie ma metadanych przekazywanych w luźnych polach.
6. Caddy ogranicza request body do 26 MiB i ustawia read_timeout 10 min z minimalną szybkością 45 KiB/s dla uploadu. request_body oraz timeouts są oznaczone jako experimental od Caddy 2.10.0; compose musi używać co najmniej caddy:2.10-alpine, a implementacja uruchomi caddy validate i test realnego requestu >26 MiB. Caddy body cap jest drugą linią, handler aplikacyjny chroni również przy pominięciu proxy.
7. Limit na IncomeRecord (20 files/50 MiB) zależy od DB i jest sprawdzany ponownie w transakcji po serializacji. Nie zastępuje limitów na etapie parsera.

Kroki 1–5 obowiązują zgodnie z dokumentacją Django dla upload handlers i DATA_UPLOAD_MAX_MEMORY_SIZE: https://docs.djangoproject.com/en/5.2/topics/http/file-uploads/#upload-handlers oraz https://docs.djangoproject.com/en/5.2/ref/settings/#data-upload-max-memory-size. Caddy max_size zwraca 413: https://caddyserver.com/docs/caddyfile/directives/request_body.

## Walidacja formatu i zasoby

Brak nowych bibliotek: requirements.txt nie zawiera parsera obrazów/PDF, a ten bolt nie wprowadza kosztu zależności. Kontrakt MVP to bounded structural recognition, nie pełne dekodowanie ani sanitization. Plik jest niezaufany; wymuszony download i nosniff ograniczają ryzyko osadzenia aktywnej treści w originie aplikacji, ale nie obiecują wykrycia malware ani wszystkich uszkodzeń.

- PNG: sprawdź 8-bajtowy signature, kolejność/zakres chunków, IHDR długości 13, CRC chunków, co najmniej jeden IDAT, IEND długości zero dokładnie na końcu; sprawdź width/height > 0, każdy wymiar do 12 000 px i product do 40 megapikseli. Nie dekompresuj IDAT; uszkodzenie skompresowanego strumienia z poprawnym opakowaniem może przejść.
- JPEG: bounded marker scan z kontrolą długości segmentów, SOI, SOS, EOI na końcu, znaleziony SOF i wymiary do 12 000 px/40 MP; odrzucaj ucięty segment, brak EOI i bajty po EOI. Nie dekoduj entropy stream, więc nie stwierdzamy pełnej poprawności obrazu.
- PDF: maksymalnie 10 MiB; header %PDF-1.x na początku oraz %%EOF w końcowym oknie z samym whitespace po nim; brak parsera xref/object/page i brak gwarancji, że dokument jest w pełni poprawny lub wolny od polyglotów.
- Dla wszystkich formatów czas scan jest liniowy do 10 MiB; bufor odczytu ≤64 KiB; metadata format/extension mismatch jest rejected. Sygnatura i basic structure nie są AV scanningiem.
- Nazwa jest Unicode-normalizowana, bez separatorów, znaków sterujących i ścieżek; pusta po normalizacji jest odrzucana. Storage key pochodzi z UUID, nie z nazwy. SHA-256 liczony przy zapisie służy integrity check, nie jest dowodem autentyczności i nie trafia do API/audytu.

Testy muszą sprawdzić poprawne sygnatury z uciętym/uszkodzonym końcem, uszkodzone chunk CRC/marker lengths, brak końcowego znacznika, ekstremalne wymiary i skompresowany stream przekraczający limity bez alokowania/dekodowania jego wymiarów.

## Model danych

IncomeAttachment jest child IncomeRecord; household, parent i miesiąc odpowiadają URL i nie zmieniają się. FK do Household, IncomeRecord, created_by i removed_by używają PROTECT.

| Pole | Kontrakt |
| --- | --- |
| id | UUID PK. |
| household, income_record | Niezmienne właścicielstwo. |
| upload_batch_id | Losowy UUID operacji, wspólny dla maksymalnie pięciu załączników; koreluje metadata z filesystem claim, nie tworzy agregatu ani publicznego batch resource. |
| original_name | CharField(255), bezpieczna nazwa prezentowana. |
| media_type | Kanoniczne image/png, image/jpeg lub application/pdf. |
| size_bytes | Rzeczywisty dodatni rozmiar, maksymalnie 10 MiB. |
| storage_key | Unikalny losowy klucz względem MEDIA_ROOT, nigdy w odpowiedzi/audycie. |
| content_sha256 | 64 małe znaki hex. |
| availability_state | available albo removed; jawny stan logicznego dostępu, niezależny od kwarantanny. |
| created_at, created_by | Czas i aktor utworzenia. |
| removed_at, removed_by | Null razem dla available; wymagane dla removed. |
| storage_deleted_at | Null dla available i oczekującego cleanup; timestamp po potwierdzonym unlink. |

Constraints parują state z removed_at/by oraz storage_deleted_at. Indeksy: household + income_record + availability_state + created_at + id, storage_deleted_at dla cleanup, upload_batch_id do reconciliation. Nie używać FileField/public URL.

AuditLog używa object_type income_attachment, actions created/deleted. Snapshot zawiera household, income, attachment ID, bezpieczną nazwę, typ, size i stan logiczny; bez bajtów, SHA, storage key, ścieżki i batch ID. Metadata i audit są atomowo w PostgreSQL. Audit failure rollbackuje całą partię.

## Prywatne storage, ownership i upload transaction

Wolumen media_data jest trwały po restarcie i jest objęty procedurą backup/restore, która zatrzymuje zapisy przed spójną kopią PostgreSQL + volume. Caddy obsługuje wyłącznie API i frontend; żadna statyczna ścieżka nie serwuje storage. Final key: income-attachments/{household_uuid}/{upload_batch_uuid}/{attachment_uuid}; staged files i manifest: MEDIA_ROOT/.incoming/{upload_batch_uuid}/; stabilny lock file dla batcha: MEDIA_ROOT/.incoming/locks/{upload_batch_uuid}.lock. Lock file powstaje i jest fsync przed pierwszym bajtem; nigdy nie jest usuwany razem z manifestem.

1. Middleware tworzy manifest z losowym upload_batch_id i otwiera per-claim advisory lock przed parserem. Trzyma ten sam lock file descriptor przez odbiór bajtów, walidację, promotion oraz finalizację DB albo kompensację. Nie stosuje lease expiration ani takeoveru aktywnego locka.
2. Handler zapisuje chunks bezpośrednio w claim directory, odświeża heartbeat, actual byte counters i nazwy plików. Claim chroni także parser temporary files, bo handler nie używa globalnych handlerów Django. Nawet jeśli operacja jest starsza niż 24h, cleaner pomija claim, jeżeli nie może zdobyć exclusive lock.
3. Po przejściu walidacji atomowo promuj pliki na tym samym wolumenie. Flush/fsync pliku przed rename, potem fsync każdego katalogu zawierającego nowy entry oraz kolejno wszystkich utworzonych ancestor directories aż do MEDIA_ROOT. Manifest zapisuje kompletną listę final keys i jest fsync przed DB. Dopiero po zakończeniu tych operacji rozpoczyna się transakcja.
4. W krótkiej transakcji locked_access blokuje Household i ponownie sprawdza rolę. Następnie zablokuj AccountingYear (select_for_update) i rozwiąż month w jego zakresie. Zablokuj nieusunięty IncomeRecord w household/month; missing, foreign lub deleted parent zwraca 404 przed sprawdzeniem stanu. Dla DELETE attachment rozwiąż także dostępny child scoped do parent przed sprawdzeniem okresu. Dopiero potem wymagaj active month (409) i sprawdź bieżące limity count/bytes; ta kolejność zachowuje kontrakt 014 i rozstrzyga close/delete wyścigi.
5. Wstaw wszystkie rows IncomeAttachment z upload_batch_id i audyty w jednej transakcji. Ten sam lock year stosują close/reopen; household/year/parent lock serializuje upload z zamknięciem i soft-delete income. Parent delete oznacza wszystkie child rows jako removed i zapisuje audyty w tej samej transakcji.
6. Commit DB jest transferem claimu: wszystkie storage keys mają już trwałe bajty i rows, zanim claim lock zostanie zwolniony. Każdy skaner finalnych obiektów wyprowadza upload_batch_id z klucza i zdobywa ten sam stabilny lock przed DB lookup/unlink; brak manifestu nie omija blokady. Następnie odczytuje DB i nie kasuje available ani cleanup-pending row.
7. Błąd przed commit wycofuje całą partię metadata+audit i próbuje skasować wszystkie staging/promoted keys pod utrzymanym claim lockiem. Jeżeli cleanup zawiedzie, manifest i claim pozostają. Odrzucona partia nie emituje successful business audit.

Zapewnienie fencing wynika z nieprzekazywanego lock descriptor i losowego upload_batch_id: tylko proces, który utrzymuje claim lock, może zatwierdzić jego rows; każda nowa próba otrzymuje nowy ID. Proces żywy, w tym zapauzowany, zatrzymuje cleaner bez względu na heartbeat/grace. Po śmierci procesu system operacyjny zwalnia lock, więc stary request nie może wznowić pracy z tym ID.

## Odczyt, logiczne usunięcie i reconciliation

GET/list wymaga read access, scoped household/year/month/income i nieusuniętego parenta; działa także przy inactive/closed miesiącu. Download wymaga również available attachment. Zwracaj canonical MIME, FileResponse jako attachment, RFC 5987 safe filename, X-Content-Type-Options: nosniff i Cache-Control: private, no-store. Odpowiedź nie zawiera URL-a ani redirect do storage.

DELETE attachment wymaga active month po wcześniejszym potwierdzeniu istniejącego parenta i child. W transakcji ustaw availability_state=removed, removed_at/by oraz zapisz audit atomowo; storage_deleted_at pozostaje null. Po commit best-effort callback zdobywa ten sam per-object lock co reconciler, re-checkuje pending state, próbuje unlink, a następnie w nowej krótkiej transakcji ustawia storage_deleted_at. Wyjątki callbacka są przechwytywane i logowane bez danych prywatnych; nigdy nie zmieniają 204 już zatwierdzonego DELETE. Awaria unlink albo update storage_deleted_at pozostawia trwały cleanup-pending row i nie przywraca dostępu.

Use-case DELETE IncomeRecord w bolt 014 musi w tej samej transakcji logicznie usunąć wszystkie available attachments i zapisać ich audyty. Po commit best-effort usuwa bajty; callback izoluje każdą awarię i nie zmienia sukcesu DELETE parenta. Pliki nie są zachowane po soft-delete przychodu; metadata/audit history pozostaje. Hard purge nie jest w zakresie. Backup może zawierać usunięte bajty do rotacji.

Management command reconcile_income_attachment_storage ma dry-run i działa porcjami:
1. Dla removed rows z storage_deleted_at=null zdobądź per-object OS lock, ponownie sprawdź pending state, wykonaj unlink idempotentnie (brak pliku oznacza już skasowany), a następnie ustaw storage_deleted_at. Błąd unlink albo DB update pozostawia pending row do kolejnej próby; nie twórz ponownie business audit.
2. Dla batch claims zdobądź exclusive claim lock non-blocking; zajęty lock pomiń bez względu na wiek. Jeżeli DB wskazuje dostępne lub pending cleanup rows, zachowaj final keys i odtwórz/utrzymaj claim state. Jeśli rows nie istnieją, usuń zawartość starego, osieroconego claimu dopiero po 24h. Po każdym DB lookup/odczycie claim trzymaj lock przez decyzję i unlink.
3. Obiekt bez manifestu nadal mapuje upload_batch_id ze ścieżki i wymaga tego stabilnego batch lock; jeśli key nie pozwala na mapowanie, wymagany jest per-object lock. Po locku wykonaj DB lookup. Zachowaj każdy key z available/pending row; zgłoś brakujące bajty pod aktywnym metadata jako integrity error. Usuwaj tylko nieowned object starszy niż 24h. 24h jest grace policy dla procesu już nieżyjącego, nigdy metodą przejęcia aktywnego locka.

Dla obiektów z opublikowanym metadata cleanup callback i command są procesami unlink; pre-commit compensation wykonuje uploader pod jego aktywnym batch lockiem. Callback i command używają per-object locka oraz rechecku DB. Command należy uruchamiać cyklicznie jako zadanie operatora; MVP nie dodaje nowego kontenera/workera. Wyjątek after_commit callback jest bezpiecznie konsumowany; retry usuwa brakujący już plik jako sukces i może uzupełnić storage_deleted_at.

## Błędy HTTP i bezpieczeństwo

- 400: niepoprawny multipart, pusty/uszkodzony envelope, filename, typ/rozmiar/liczba ponad limit.
- 403: Member/Viewer próbuje mutacji, brak uwierzytelnienia lub nieprzejście CSRF.
- 404: brak/obcy year, month, income lub attachment, soft-delete parenta, logical removal; ten wynik ma pierwszeństwo przed konfliktem inactive/closed dla missing/deleted resources.
- 409 income_period_not_active: parent/attachment istnieją w podanym scope, ale miesiąc nie jest active.
- 413: Caddy body cap; klient rozpoznaje status niezależnie od response envelope proxy.
- 500: błąd metadata/business audit przed commit; cała transakcja jest rollback.
- 503: storage niedostępne przed publikacją; metadata/audit brak, claim pozostaje do cleanup/retry.
- Błędy unlink/post-commit DB timestamp nie zmieniają zakończonego 204/parent-delete; pozostawiają pending row.
- Odrzucony upload nie tworzy successful business audit. Log może zawierać household/user/request ID i reason code, nigdy nazwę, MIME klienta, path ani bytes.

## Strategia testów

1. Multipart PNG/JPG/JPEG/PDF, właściwy parent i household, canonical MIME, size, batch ID i SHA.
2. Handler bez Caddy i z brakującym/fałszywym Content-Length: limity per-file/batch/file-count/time interrupt zanim przekroczone bajty zostaną zapisane; max chunk/memory, CSRF failure cleanup, niepowstające /tmp copies i unauthorized requests odrzucone przed parserem.
3. Format tests: valid envelope; truncated file; uszkodzone CRC/segment length/brak IEND/EOI/EOF; bytes after EOF; 0/over-limit dimensions, 40MP edge i przekroczenie limitu parsera bez dekompresji obrazów.
4. Role/tenant isolation, cross-parent UUID, parent deleted, child removed; GET/download w inactive/closed; upload/delete write rejection. Missing/foreign/deleted parent × inactive/closed musi zwracać 404; istniejący parent/child × inactive/closed zwraca 409.
5. Deterministyczne PostgreSQL concurrency tests: close vs final upload, income delete vs final upload, równoległe uploady limitu; filesystem I/O nie dzieje się pod DB locks.
6. Claim tests z osobnymi procesami: cleaner pomija aktywny/paused upload nawet po 24h; uploader wznowiony z utrzymanym lockiem może zatwierdzić; cleaner zdobywający lock po crashu usuwa tylko po grace i uploader nie może wznowić starego batch ID; cleaner między promotion a commit nie usuwa kluczy.
7. Audit failure rollbackuje całą partię. Fail unlink po commit, fail DB update po udanym unlink, restart + retry zachowują odpowiedź mutation, pending row i dokładnie jeden business audit.
8. Soft-delete parent logicznie odcina wszystkie dzieci atomowo; cleanup powtarzalny. Reconciliation dry-run/execution chroni available/pending objects, raportuje missing bytes, usuwa tylko nieowned po 24h; backup/restore zachowuje bajty i metadata.
9. Caddy validate oraz integracyjny test request body >26 MiB zwracający 413; migration check, focused tests, PostgreSQL races, Ruff i scripts/quality.ps1; pełne testy i zmienione pliki przed Stage 5.

## Kolejność implementacji

1. Model, constraints, indeksy, migracja i custom bounded upload handler/claim; testy pierwszej granicy parsera przed API.
2. Private storage adapter, fsync/promotion/fencing i reconciliation command; testy multi-process paused uploader/cleaner.
3. API serializers, response schemas, tenant-scoped routes, upload/list/download/remove i transakcyjny audit.
4. Integracja soft-delete IncomeRecord z attachment lifecycle oraz izolowane on_commit cleanup callbacks.
5. Caddy version/min-size/timeouts config i realny >limit test, testy rollback/race/retention, quality i pełny Stage 5 report.

## Uzasadnienie decyzji ADR

Zachowujemy ADR-002/004/006: synchronizacja z Households/AccountingYear, recheck roli i atomowy audit. Przejście lokalnego filesystemu przez claim lock oraz prywatne API jest konsekwencją istniejącej infrastruktury media_data. Nie wprowadzamy nowego zewnętrznego bounded context, workera ani usługi skanowania; dlatego Stage 3 ADR analysis może zostać pominięty, jeśli reviewer nie wskaże nowej decyzji wymagającej osobnego ADR.

## Zgodność ze story 005

Wiele plików należy do jednego income/household; batch rows i audyty są all-or-nothing; limity są egzekwowane przed parserem, podczas walidacji oraz pod lockiem dla łącznych limitów; odczyt jest wyłącznie autoryzowany; pliki są prywatne i trwałe; failure cleanup jest retryable, a cleaner nie może usunąć aktywnego claim ani owned object.
