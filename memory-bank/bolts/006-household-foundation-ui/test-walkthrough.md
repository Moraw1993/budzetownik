---
stage: test
bolt: 006-household-foundation-ui
created: 2026-09-21T19:23:00Z
status: accepted
---

# Raport testów: konta, gospodarstwa i zaproszenia

## Podsumowanie

- **Testy aplikacji**: 86/86 zakończonych powodzeniem — 68 Django, 17 izolowanych scenariuszy UI i 1 pełny scenariusz UI przez rzeczywiste HTTPS, API oraz PostgreSQL.
- **Runtime**: 6/6 kontroli zakończonych powodzeniem.
- **Kontrola jakości**: Ruff format/check, Prettier, ESLint, Stylelint i TypeScript zakończone powodzeniem przez scripts/quality.ps1.
- **Coverage**: nie mierzono pokrycia kodu w tym bolcie; kryteria sprawdzono scenariuszami funkcjonalnymi i integracyjnymi.
- **Stan usług po testach**: db, backend i frontend healthy; migrate zakończone kodem 0; proxy działa na 127.0.0.1:8080 i 127.0.0.1:8443.

## Pliki testów

- [x] `frontend/tests/foundation.spec.ts` — formularze kont, błędy, sesja, role, zaproszenia, wyścigi żądań, responsywność i klawiatura z kontrolowanymi odpowiedziami API.
- [x] `frontend/tests/live-foundation.spec.ts` — logowanie, puste konto, utworzenie gospodarstwa, wystawienie linku, utworzenie zaproszonego konta, rola Viewer i blokada ponownego użycia przez rzeczywisty stos aplikacji.
- [x] `backend/households/tests/test_invitations.py` oraz pozostałe testy Django — autoryzacja, CSRF, role, izolacja, link wygasły, odwołany i zużyty oraz reguły domenowe.
- [x] `scripts/verify_runtime.py` — HTTPS, health, trwałość bazy i pliku, odpowiedź 503 przy awarii bazy, odtworzenie oraz idempotentna konfiguracja sekretów.

## Walidacja kryteriów akceptacji

- ✅ **Pusta i istniejąca instalacja**: rzeczywisty test utworzył użytkownika bez gospodarstw, pokazał bezpośrednio formularz gospodarstwa i przeszedł pełny przepływ; testy izolowane pokryły konfigurację pierwszego konta i logowanie.
- ✅ **Zachowanie pól formularza**: login pozostaje po błędzie walidacji, hasło jest czyszczone, a focus trafia na komunikat błędu.
- ✅ **Wylogowanie i historia**: chronione dane znikają, ponowne pokazanie strony sprawdza sesję, a nieudane wylogowanie nie udaje sukcesu.
- ✅ **Etykiety, klawiatura i bezpieczne błędy**: pola mają etykiety; Enter wysyła formularz; tabela ma focus i poziome sterowanie klawiaturą; odpowiedź 5xx nie ujawnia treści serwera.
- ✅ **Tworzenie i wybór gospodarstwa**: sprawdzone w izolowanym teście i przez rzeczywiste API; naprawiono wykryty podczas odbioru przycisk ukrywający formularz w stanie pustym.
- ✅ **Ochrona przed spóźnioną odpowiedzią**: zakończenie starego odczytu i zapisu nie przywraca poprzedniego kontekstu.
- ✅ **Role i odmowa API**: Owner zarządza rolami, pozostałe role mają odczyt; ochrona ostatniego Ownera i odebranie uprawnień odświeżają widok bez pozornego sukcesu.
- ✅ **Wystawienie, kopiowanie i odwołanie zaproszenia**: termin ważności i rola są widoczne; sprawdzono link, fallback schowka, anulowanie potwierdzenia i odwołanie.
- ✅ **Przyjęcie i błędne linki**: rzeczywisty link utworzył konto Viewer i wybrał właściwe gospodarstwo; token zniknął z adresu; ponowne użycie pokazało czytelny błąd. Backend potwierdził także odwołanie i wygaśnięcie bez zmiany danych.

## Test rzeczywistego przepływu

Test utworzył dwa unikalne konta o prefiksie `e2e_` i jedno gospodarstwo `Dom testowy ...`. Po scenariuszu usunął gospodarstwo, zaproszenie, członkostwa i oba konta. Osobna kontrola bazy potwierdziła brak użytkowników i gospodarstw testowych. Istniejące dane użytkownika nie były zmieniane.

Pierwsza próba ujawniła błąd stanu pustego: formularz nowego gospodarstwa był otwarty, ale widoczny przycisk „Nowe gospodarstwo” ukrywał go. Po poprawce przycisk nie jest renderowany bez istniejących gospodarstw. Frontend przebudowano, a pełny test powtórzono z wynikiem pozytywnym.

## Kontrola runtime

- ✅ certyfikat lokalnego HTTPS, health API i shell aplikacji;
- ✅ zachowanie rekordu PostgreSQL i pliku po odtworzeniu kontenerów;
- ✅ odpowiedź 503 bez szczegółów podczas niedostępności bazy;
- ✅ odzyskanie po ponownym uruchomieniu bazy oraz zachowanie danych;
- ✅ ponowna konfiguracja nie zastępuje istniejących sekretów;
- ✅ brak wymaganej konfiguracji kończy się czytelnym błędem.

## Otwarte problemy

Brak otwartych błędów naruszających stories 001–003. Ostrzeżenie npm dotyczy cyklu wsparcia użytej wersji ESLint i nie jest błędem kontroli. Pokrycie procentowe nie było kryterium bolta i nie zostało zmierzone.

Użytkownik zatwierdził raport 2026-09-21T19:28:14Z. Bolt i stories 001–003 mają status `complete`.
