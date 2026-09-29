---
bolt: 004-foundation-api
created: 2026-09-11T19:20:12+02:00
status: accepted
superseded_by: null
---

# ADR-003: Ochrona tokenów zaproszeń

## Kontekst

Lokalne zaproszenie jest przekazywane jako kopiowany link i może tworzyć konto albo członkostwo. Token jest więc sekretem dostępowym: nie może zostać zapisany w bazie, logu, audycie, odpowiedzi listującej ani przypadkowo przesłany jako część ścieżki żądania. Równoległe użycie linku nie może utworzyć dwóch członkostw.

ADR-001 wymaga sesji Django i jawnego CSRF dla anonimowych zapisów. ADR-002 wymaga blokowania gospodarstwa oraz ponownego sprawdzania kontekstu dostępu dla zapisów agregatu.

## Decyzja

Link zaproszenia ma token w fragmencie lokalnego URL: `https://localhost:8443/accept-invitation#{token}`. Frontend odczytuje fragment po stronie klienta i wysyła token wyłącznie w treści POST do endpointu przyjęcia przez lokalny HTTPS.

Backend generuje token kryptograficznie bezpiecznie i zapisuje wyłącznie jego HMAC-SHA-256. Porównanie jest bezpieczne czasowo, a logowanie aplikacji usuwa token z adresów, payloadów i komunikatów wyjątków. Przyjęcie wykonuje się atomowo po zablokowaniu gospodarstwa i zaproszenia; po blokadzie ponownie sprawdza skrót oraz ważność zaproszenia.

## Uzasadnienie

Fragment URL nie jest wysyłany do serwera przy wejściu na stronę ani w nagłówku Referer. Dzięki temu mechanizm ogranicza ryzyko wycieku sekretu bez dodawania zewnętrznej infrastruktury, co odpowiada zakresowi lokalnego MVP. Jednocześnie skrót w bazie ogranicza skutki ewentualnego odczytu danych, a transakcja i ograniczenie unikalności członkostwa chronią przed podwójnym użyciem linku.

## Rozważone alternatywy

| Alternatywa | Zaleta | Wada | Powód odrzucenia |
| --- | --- | --- | --- |
| Token w ścieżce endpointu API | Prosty link i routing | Może trafić do logów serwera, proxy i narzędzi monitorujących | Nie spełnia wymagania ograniczenia tokenu w logach. |
| Jawny token w kolumnie bazy | Ułatwia diagnostykę | Ujawnia sekret przy odczycie bazy i kopii zapasowej | Sekret nie może być przechowywany wprost. |
| Wysyłka e-mail z tokenem | Znany wzorzec zaproszeń | Wymaga SMTP i zewnętrznego kanału poza zakresem MVP | PRD i uzgodnienia określają kopiowany link bez e-maila. |

## Konsekwencje

### Pozytywne

- Token nie jest częścią ścieżki HTTP ani trwałych danych aplikacji.
- Mechanizm działa bez zewnętrznego dostawcy i zachowuje lokalny charakter MVP.
- Jedna transakcja chroni przed częściowym stanem i równoległym przyjęciem.

### Negatywne

- Frontend musi obsłużyć fragment URL i przekazać token w treści żądania.
- Diagnostyka problemów z linkiem wymaga bezpiecznych identyfikatorów zaproszenia zamiast wartości tokenu.

### Ryzyka

- Użytkownik może przekazać link nieuprawnionej osobie; ograniczeniami są termin siedmiu dni, odwołanie przez Ownera i jednorazowe użycie.
- Błędne logowanie requestów może mimo decyzji ujawnić body; testy i konfiguracja logów muszą sprawdzać redakcję tokenu.

## Powiązania

- **Stories**: 007-issue-invitation, 008-accept-invitation.
- **Standardy**: coding-standards.md, tech-stack.md.
- **Poprzednie ADR-y**: ADR-001, ADR-002.
