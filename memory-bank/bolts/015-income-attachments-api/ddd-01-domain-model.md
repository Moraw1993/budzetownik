---
unit: 002-monthly-income-api
bolt: 015-income-attachments-api
stage: model
status: complete
updated: '2026-10-07T20:13:37Z'
---

# Stage 1 — model domenowy prywatnych załączników przychodu

## Bounded Context

Załączniki są poddomeną i częścią bounded context `Monthly Income`; nie tworzą osobnego bounded context. Istniejący `IncomeRecord` pozostaje jedynym korzeniem agregatu i właścicielem biznesowym załączników przypisanych do dokładnie jednego gospodarstwa. Metadane załącznika są dziećmi tego agregatu. Bajty pliku pozostają poza PostgreSQL; baza przechowuje metadane. Dla lokalnego MVP obowiązuje trwały filesystem, bez publicznego hostingu ani zewnętrznego dostawcy.

Zakres obejmuje wiele plików przy jednym wpisie, bezpieczne przyjęcie dozwolonych formatów PNG, JPG/JPEG i PDF, prywatny odczyt przez autoryzację gospodarstwa, usuwanie i sprzątanie zawartości oraz brak osieroconych plików. OCR, parsowanie dokumentów, udostępnianie publicznym linkiem i zewnętrzne usługi skanowania pozostają poza zakresem, chyba że analiza Stage 2 wykaże wymagany lokalny mechanizm ochrony.

## Język dziedzinowy

| Termin | Znaczenie |
| --- | --- |
| Załącznik przychodu (`IncomeAttachment`) | Jedna prywatna pozycja metadanych powiązana z dokładnie jednym `IncomeRecord`; zawartość pliku jest przechowywana poza bazą. |
| Zawartość pliku | Bajty dokumentu w prywatnym storage. Nie są wartością domenową ani częścią rekordu audytu. |
| Metadane załącznika | Identyfikator, nazwa prezentowana, rozpoznany typ, rozmiar, data dodania i opcjonalny opis. Nie ujawniają ścieżki storage. |
| Partia uploadu | Jedno żądanie dodania jednego lub wielu plików do tego samego przychodu. Proponowana reguła: cała partia jest widoczna albo żaden jej plik nie jest widoczny. |
| Prywatny odczyt | Pobranie wymaga bieżącej autoryzacji do gospodarstwa i wpisu; sam identyfikator pliku ani znajomość nazwy nie daje dostępu. |
| Osierocona zawartość | Obiekt bez ważnego właściciela ani rekordu staging/cleanup/retention claim. Aktywny staging, kwarantanna i zaakceptowana retencja są rozpoznawalnymi stanami własności, a nie orphanem. Metadane wskazujące brakujące bajty są osobnym błędem integralności. Żadna zawartość nie jest publiczna. |

## Encje

### `IncomeAttachment` (nowa encja podrzędna wpisu przychodu)

Tożsamość: UUID. Proponowane właściwości:

- `income_record_id` — dokładnie jeden istniejący wpis; powiązanie jest niezmienne po utworzeniu;
- `household_id` — tenant właścicielski, zgodny z gospodarstwem wpisu przychodu;
- `original_name` — bezpieczna nazwa prezentowana, oczyszczona z separatorów ścieżek i znaków sterujących;
- `media_type` — typ rozpoznany po zawartości, spośród PNG, JPEG i PDF; deklaracja klienta jest tylko wskazówką;
- `size_bytes` — dodatnia liczba bajtów, nieprzekraczająca limitu;
- `description` — opcjonalny opis metadanych, jeśli Stage 2 potwierdzi go w kontrakcie UI/API; bez treści wrażliwej wymaganej do identyfikacji wpisu;
- `storage_reference` — niejawne, losowe odwołanie do prywatnego obiektu, niedostępne w odpowiedzi użytkowej;
- `content_digest` — opcjonalny skrót integralności, którego algorytm i cel należy zatwierdzić w Stage 2;
- `created_at` i `created_by` — czas dodania i wykonawca;
- availability_state — jawny stan logiczny available albo removed, niezależny od ewentualnej kwarantanny zawartości;

- removed_at i removed_by — aktor i czas logicznego odebrania dostępu, null tylko dla available;
- storage_deleted_at — null, gdy zawartość pozostaje dostępna lub cleanup oczekuje; timestamp potwierdza fizyczne usunięcie po logical removal;
- created_at i created_by — czas dodania i wykonawca.

Załącznik nie przechowuje kopii kwoty, źródła ani daty otrzymania przychodu. Te dane należą do `IncomeRecord`; metadane załącznika nie mogą stać się alternatywnym źródłem prawdy.

## Obiekty wartości

| Obiekt wartości | Właściwości | Ograniczenia |
| --- | --- | --- |
| `AttachmentFileName` | Nazwa przesłana i nazwa prezentowana | Traktowana jako niezaufana; normalizacja blokuje `..`, ścieżki, znaki sterujące i wstrzyknięcie nagłówków. Nie jest nazwą obiektu storage. |
| `AttachmentMediaType` | Typ zawartości rozpoznany przez serwer | Tylko PNG, JPEG (`.jpg`/`.jpeg`) lub PDF; rozszerzenie i `Content-Type` klienta nie potwierdzają formatu. |
| `AttachmentSize` | Liczba bajtów | Większa od zera; górne granice na plik, partię i liczbę plików wymagają decyzji przed implementacją. |
| `AttachmentDescription` | Opcjonalny, ograniczony tekst wyświetlany | Brak HTML/wykonywania; długość i obecność zależą od zatwierdzonego kontraktu. |
| `AttachmentDigest` | Skrót bajtów dla kontroli integralności | Nie zastępuje walidacji typu ani autoryzacji; algorytm i potrzeba do potwierdzenia. |
| `PrivateStorageReference` | Nieprzewidywalny identyfikator obiektu | Bez ścieżki, URL-a ani nazwy użytkownika; używany wyłącznie przez adapter prywatnego storage. |

## Agregaty

| Korzeń agregatu | Elementy | Niezmienniki |
| --- | --- | --- |
| `IncomeRecord` (istniejący, jedyny korzeń) | Zbiór metadanych `IncomeAttachment`; zawartość plików pozostaje zewnętrzna | Każdy załącznik wskazuje dokładnie ten wpis i jego gospodarstwo. Zmiana relacji załącznika na inny wpis jest zabroniona. Wymagane są: istniejący, nieusunięty wpis oraz aktywny miesiąc dla mutacji użytkownika. Liczba i łączny rozmiar nie przekraczają limitów. |

`AttachmentUploadBatch` jest granicą przypadku użycia, nie encją ani korzeniem agregatu. All-or-nothing oznacza, że metadane całej partii stają się widoczne razem albo żadne z nich. Nie oznacza transakcji rozproszonej PostgreSQL i filesystemu: prywatne obiekty staging mogą chwilowo pozostać po błędzie, lecz muszą mieć ważny staging/cleanup claim, pozostawać niedostępne dla użytkownika i podlegać kontrolowanemu reconciliation.

Załączniki są encjami podrzędnymi, a nie odrębnymi właścicielami biznesowymi. Operacje kontroluje `IncomeRecord` wraz z tenant-scoped autoryzacją. Równoległe uploady do tego samego wpisu nie mogą przekroczyć limitu liczby ani rozmiaru; mechanizm serializacji należy ustalić w Stage 2.

## Reguły domenowe i cykl życia

1. Dodanie, usunięcie lub edycja metadanych przez użytkownika wymaga nieusuniętego `IncomeRecord`, jego aktywnego miesiąca i Owner/Administrator. Member/Viewer nie mogą mutować załączników. Ten sam wpis w okresie inactive/closed pozostaje dostępny do autoryzowanego odczytu tylko dla ról mających read access.
2. Dostęp sprawdza się w gospodarstwie, rodzicu i bieżącym stanie okresu. Długie staging/I/O nie może opierać końcowego zatwierdzenia na nieaktualnej autoryzacji: publikacja partii ponownie sprawdza uprawnienia, nieusunięty wpis oraz active month w granicy spójności z zamknięciem okresu i usunięciem rodzica. Konkretna blokada zgodna z ADR-006 należy do Stage 2; nie wolno trzymać blokad podczas długiego I/O.
3. Użytkownik uprawniony do odczytu przychodu może pobrać załącznik tylko przez autoryzowany przepływ aplikacji. Dostęp do storage nie jest publiczny, a URL lub UUID nie stanowi tokenu dostępu. Odczyt pozostaje dozwolony przy inactive/closed miesiącu.
4. Jeden plik staje się widoczny dopiero po sprawdzeniu rozmiaru i rzeczywistego typu zawartości oraz przygotowaniu go w prywatnym storage i metadanych. Zaufanie do deklaracji MIME klienta jest zabronione.
5. All-or-nothing partii gwarantuje atomową widoczność metadanych: po błędzie cała partia pozostaje niewidoczna. Obiekty tymczasowe mają rozpoznawalny staging/cleanup claim; proces reconciliation nie usuwa aktywnego stagingu ani obiektów objętych prawidłową retencją. Szczegóły kompensacji należą do Stage 2.
6. Usunięcie pojedynczego załącznika najpierw logicznie odbiera użytkownikom dostęp, zapisując stan metadanych i biznesowy audyt atomowo. Fizyczne kasowanie może być asynchroniczne; jego opóźnienie lub błąd nie przywraca dostępu. Sprzątanie techniczne niewidocznej zawartości może przebiegać także po zamknięciu miesiąca.
7. Zmiękko-usunięty `IncomeRecord` nie udostępnia zwykłej listy ani plików. Czy pliki kasować od razu, zachować do określonego terminu, czy usuwać przy trwałym purge wpisu, pozostaje decyzją retencji Stage 2. Retencja i aktywne staging są jawnymi własnościami; reconciliation nie może traktować ich jak orphanów.
8. Publikacja metadanych całej partii oraz niezmienny biznesowy audit powstają w jednej transakcji; błąd audytu wycofuje udaną operację. Logiczne odebranie dostępu do metadanych i audit usunięcia również są atomowe. Odrzucony upload nie generuje success audit. Audyt i logi nie zawierają bajtów, sekretów, prywatnej ścieżki storage ani pełnej zawartości dokumentu.

## Zdarzenia domenowe

| Zdarzenie | Wyzwalacz | Dane |
| --- | --- | --- |
| `IncomeAttachmentsAdded` | Cała partia została zwalidowana, zapisana i ujawniona | Household ID, IncomeRecord ID, identyfikatory załączników, rozpoznane typy i rozmiary, actor ID; bez zawartości i ścieżek. |
| `IncomeAttachmentRemoved` | Dostęp do wskazanego załącznika został logicznie odebrany i business audit zapisany atomowo | Household ID, IncomeRecord ID, attachment ID, actor ID i stan cleanup `pending`; bez wyniku przyszłego sprzątania. |
| `IncomeAttachmentRejected` | Upload odrzucono przed utworzeniem widocznych metadanych | Powód walidacji w kodzie błędu, identyfikator operacji i actor ID; bez surowych bajtów ani nazw wrażliwych w logach bezpieczeństwa. |
| `IncomeAttachmentCleanupRequired` | Kompensacyjne usunięcie nie powiodło się | Niejawny storage reference i czas/identyfikator korelacji, widoczne wyłącznie procesowi sprzątającemu. |
| `IncomeAttachmentStorageCleanupCompleted` | Prywatny obiekt po logicznym usunięciu został fizycznie skasowany | Attachment ID, wynik i czas; zdarzenie techniczne, nie zastępuje `IncomeAttachmentRemoved`. |

Zdarzenia służą audytowi i sprzątaniu; nie wprowadzają event-sourcingu.

## Usługi domenowe

| Usługa | Operacje | Zależności |
| --- | --- | --- |
| `AddIncomeAttachments` | Autoryzuje i sprawdza active month, waliduje wszystkie pliki, pilnuje limitów, przygotowuje batch i atomowo publikuje metadane z audytem dopiero po końcowym ponownym sprawdzeniu | `IncomeRecord`, stan `AccountingMonth`, polityka ról, repozytorium metadanych, prywatny storage, audyt. |
| `GetIncomeAttachment` | Wyszukuje po gospodarstwie i wpisie, ponownie sprawdza rolę, pobiera/strumieniuje zawartość | Repozytorium wpisów/załączników, polityka autoryzacji, prywatny storage. |
| `RemoveIncomeAttachment` | Przy active month atomowo logicznie odbiera dostęp i zapisuje audit, a następnie zleca fizyczne sprzątanie | `IncomeRecord`, stan `AccountingMonth`, repozytorium metadanych, audyt, prywatny storage lub kolejka sprzątania. |
| `ReconcileAttachmentStorage` | Wykrywa niepowodzenia kompensacji i uzgadnia osierocone metadane/obiekty | Repozytorium metadanych, prywatny storage, ograniczony operator systemowy. |

## Interfejsy repozytoriów

| Repozytorium | Encja | Metody |
| --- | --- | --- |
| `IncomeAttachmentRepository` | `IncomeAttachment` podrzędny `IncomeRecord` | Tenant-scoped list/get/create/remove, policzenie aktualnych limitów, zapis metadanych całej partii i oznaczanie oczekującego sprzątania. |
| `PrivateAttachmentStorage` | Zawartość pliku, poza bazą | Staging, commit/publikacja do prywatnego storage, autoryzowany odczyt strumieniowy, kasowanie, kontrola istnienia i uzgadnianie orphanów; nie zwraca publicznego URL. |

Nazwy są kontraktami domenowymi; implementacja może używać istniejących wzorców Django i filesystemu bez sztucznych abstrakcji, jeśli zachowa prywatność, testowalność i kompensację.

## Decyzje przekazane do Stage 2

- Limity: maksymalna liczba plików na przychód, bajty na plik, bajty na partię i dopuszczalny czas/zużycie pamięci.
- Weryfikacja: sygnatury plików i biblioteki parsujące obrazy/PDF, odporność na formaty polyglot, zip-bomb/rozmiar po dekodowaniu oraz dostępny lokalny malware scanning/kwarantanna.
- Realizacja partii: zaprojektować staging/kompensację i zachowanie po utracie procesu między filesystemem a PostgreSQL, zachowując all-or-nothing widoczności metadanych.
- Storage: trwały prywatny filesystem MVP, losowy klucz, uprawnienia katalogów, streaming, bez `MEDIA_URL` publicznego dla tych dokumentów, oraz ścieżka migracji do Object Storage.
- Równoległość: sposób atomowego rezerwowania limitów przy wielu uploadach do jednego wpisu.
- Retencja: zachowanie załączników przy soft-delete `IncomeRecord`, ręcznym usunięciu pliku, trwałym purge, błędzie storage i odtworzeniu kopii.
- Metadane: czy opis jest potrzebny w API/UI; czy skrót treści jest wymagany; które z tych pól mogą trafiać do audytu/logów.
- API: wieloczęściowy upload, lista metadanych, usunięcie, autoryzowany streaming i stabilne odpowiedzi błędów bez ujawniania obcych tenantów.

## Kryteria pokryte modelem

- Wielokrotne PNG/JPG/JPEG/PDF należą do pojedynczego wpisu i gospodarstwa.
- Nieobsługiwany typ lub przekroczony limit odrzucany jest bez częściowo widocznych metadanych.
- Pobranie wymaga aktualnej autoryzacji; inny tenant i nieuprawniona rola nie uzyskują pliku przez identyfikator ani URL.
- Błąd uploadu lub kasowania ma określoną granicę kompensacji i nie zostawia publicznej/osieroconej zawartości.
- Metadane pozostają w PostgreSQL, a zawartość poza podstawowymi tabelami i w trwałym prywatnym storage.
