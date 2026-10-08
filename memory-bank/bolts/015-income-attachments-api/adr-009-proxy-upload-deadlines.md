---
bolt: 015-income-attachments-api
created: '2026-10-08T19:54:42Z'
status: proposed
---

# ADR-009: Uporządkowane deadline’y odczytu i zapisu API

## Kontekst

Projekt używa `caddy:2.10.0-alpine`. Sam `request_body.read_timeout` ustawia deadline odczytu, lecz anulowane proxy może zakończyć obsługę bez zapisania odpowiedzi; Go HTTP/1.1 wysyła wtedy domyślne, puste 200. Baseline na Caddy 2.10.0/Go 1.24.2 odtworzył 28 takich odpowiedzi w 40 stalled/slow-drip HTTP/1.1 przy poprawnych kontrolach i niepełnym body upstreamu. Timeout odczytu działa; błędny jest status odpowiedzi.

## Decyzja

W `/api/*` jawny `route` zachowuje kolejność:

1. `request_body { write_timeout 10m }`.
2. `request_body { max_size 26MiB; read_timeout 10m }`.
3. Dotychczasowe `reverse_proxy backend:8000`.

Write deadline powstaje przed read deadline. Po upływie późniejszego read deadline próba wysłania domyślnego 200 trafia na wygasły write deadline. Nie łączymy obu opcji w jednym handlerze, który ustawia read przed write.

Listener `:8443` jawnie obsługuje `h1 h2`, odpowiadające publikowanemu portowi TCP. HTTP/3 nie jest reklamowane ani obsługiwane bez osobnego projektu ochrony i testów. Frontend pozostaje poza handlerami deadline’u API. Nie wyłączamy guardów idle/read-header ani nie ustawiamy globalnego write timeoutu.

## Alternatywy

| Wariant | Ocena |
| --- | --- |
| Tylko read deadline | Ogranicza odbiór, ale reprodukuje puste 200; odrzucony. |
| Równe read/write w jednym handlerze | Ustawia write później niż read, pozostawiając okno zapisu; odrzucony. |
| Write timeout serwera TLS | Objąłby również frontend; wybrano węższy handler API. |
| Nieograniczone buforowanie body | Zmienia zużycie zasobów i nie zapewnia obsługi błędu kopiowania w tej wersji; odrzucone. |
| Upgrade lub własny moduł Caddy | Brak zweryfikowanej minimalnej poprawki na innej wersji; nie dodajemy zależności. |

## Konsekwencje

- Write budget API obejmuje od middleware odbiór body, pracę backendu i wysłanie odpowiedzi. Read ma osobny dziesięciominutowy deadline ustawiany chwilę później. Limit 26 MiB pozostaje bez zmian.
- Deadline nie zatrzymuje handlera ani transakcji. HTTP/1.1 może odrzucić zapis dopiero przy późnej próbie wysłania; HTTP/2 resetuje strumień. Nie obiecujemy konkretnego 408/504 ani czystego zamknięcia TLS.
- Pełne body może zostać zatwierdzone, mimo że odpowiedź nie dotrze do klienta. Wynik jest wtedy niepotwierdzony. `POST` załączników pozostaje nieidempotentny: bez automatycznego retry; klient może odświeżyć listę i jawnie zdecydować o ponownym uploadzie. Sukces wymaga 201 z poprawnym JSON `results`.
- Odczyty API/download również mają write budget; zwykłe odpowiedzi frontendu go nie otrzymują.
- Gunicorn ma jawny worker timeout 660 s. Backend w prywatnej sieci nie dziedziczy deadline’ów Caddy i nie jest wspieranym wejściem użytkownika.
- Opcje są experimental w przypiętej wersji. Zmiana obrazu Caddy wymaga ponownego validate/adapt oraz prób wszystkich wspieranych protokołów.

## Dowody przed akceptacją

Realny harness używa scaled deadlines 2/6 s; produkcyjny adapt potwierdza oba deadline’y 600 s, limit 26 MiB, kolejność i h1/h2. Każdy protokół wymaga pełnych kontroli ID/bajtów/SHA, 20 stalled i 20 slow-drip, odrzucenia 26 MiB + 1 bajtu i braku odebranego finalnego 2xx dla niepełnego uploadu. Zdrowy H2 stream musi przetrwać reset sąsiada na tym samym połączeniu.

Near-boundary: pełne body w 1,7 s plus response delay 0,7 s. A/B zmienia tylko write deadline: read2/write2 odrzuca późny zapis, read2/write6 daje kompletne 200. Wewnętrzny status 200 w access logu i udany zapis upstream→Caddy nie dowodzą otrzymania HTTP 200 przez klienta.

Manifest określa cały zbiór ID, powtórzenia, protokoły, response budget i SHA konfiguracji. Braki, duplikaty, uszkodzony JSON, brak korelacji lub watchdog klienta powodują FAIL. Dowody: [raport Stage 5](ddd-03-test-report.md).

## Źródła i powiązania

- [Caddy request_body 2.10.0](https://github.com/caddyserver/caddy/blob/v2.10.0/modules/caddyhttp/requestbody/requestbody.go), [reverse proxy](https://github.com/caddyserver/caddy/blob/v2.10.0/modules/caddyhttp/reverseproxy/reverseproxy.go), [server options](https://github.com/caddyserver/caddy/blob/v2.10.0/caddyconfig/httpcaddyfile/serveroptions.go).
- [Go HTTP 1.24.2](https://github.com/golang/go/blob/go1.24.2/src/net/http/server.go), [TLS writer](https://github.com/golang/go/blob/go1.24.2/src/crypto/tls/conn.go).
- Story 005; ADR-004 atomowy audit; ADR-007 idempotencja przychodu nie obejmuje uploadu; ADR-008 soft delete.
