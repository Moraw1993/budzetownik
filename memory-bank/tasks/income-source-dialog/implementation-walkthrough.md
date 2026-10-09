# Weryfikacja implementacji

## Zmiana

ISS-2026-002. Zamiast dodatkowego bloku „Brakuje źródła?” lista Źródło dochodu zawiera akcję „+ Dodaj nowe źródło…”. Natywny modal używa istniejących ContractForm/OtherSourceForm i wspólnego API. Sentinela nie zapisuje się w source_id. Kontekst odbiorcy i początku miesiąca podpowiada nowe źródło; kwota, waluta, data i pliki szkicu przychodu pozostają niezależne.

Kompaktowe inne źródło pokazuje sześć podstawowych pól i szczegóły na żądanie. Ukryte błędy API automatycznie rozwijają szczegóły. Pełny formularz gospodarstwa korzysta z tych samych definicji pól i nie zmienia reguł danych. Umowa zachowuje null end_date; dodano etykietę „opcjonalna” i wskazówkę dostępną przez aria-describedby.

Dialog blokuje tło, skupia i przywraca fokus, chroni szkic potwierdzeniem i blokuje zamknięcie podczas zapisu. Potwierdzenie czyni edycję starego szkicu inert. Dialog firmy pozostaje dostępny z umowy i przywraca fokus do firmy.

## Dowody

- Projekt v2: inne źródło8.4/10, umowa8.2/10, accepted; [review.md](evidence/ui-design/review.md).
- Rzeczywisty build interfejsu, dane wyłącznie syntetyczne, API mockowane w Playwright: actual-other-1440/390.jpg, actual-contract-1440/390.jpg w evidence/ui-design.
- scripts/quality.ps1: PASS (formatter, Ruff, ESLint, Stylelint, typecheck, probes). Istniejący probe wymagał lokalnej normalizacji LF, bez różnicy Git lub zmiany logiki.
- Docker frontend build: PASS, obraz sha256:542538510bb72629c4803494d1956634e219d83a62d4d68740ce43ea7b5c991f.
- 72 testy PASS,2SKIP: income-source-dialog, periods-income, periods-recovery, periods-api, periods-render, records, family, foundation. Dwa zaimportowane testy live pominięte z braku prywatnej konfiguracji odbioru; ten task nie deklaruje ponownego odbioru rzeczywistego API ani wyników backendu z poprzedniego bolta.
- Pięć nowych przypadków w income-source-dialog.spec.ts: szkic/pliki/fokus/geometria/Escape1440i390, umowa/firmy/null1440i390, ukryty błąd API. Pending i utrata roli w periods-recovery.
- Szeroki ponowny przebieg po poprawie konfiguracji testów:72PASS, exit0. Pierwsza próba serwera Next dev była przerwana po błędzie środowiska Windows (odmowa kanonizacji katalogu); finalny test korzystał z izolowanego kontenera produkcyjnego frontendu na8098.

## Granice

Brak zmian modelu, migracji i reguł finansowych. Bolt016 pozostaje ukończony;017 nie jest rozpoczynany tym taskiem. Zastane dokumenty użytkownika i pliki pnpm pozostają poza commitem. Finalna niezależna recenzja i integracja są osobno zapisane po ich rzeczywistym wykonaniu.
