---
stage: test
bolt: 002-foundation-api
created: 2026-09-10T05:53:20.129Z
---
# Wyniki testów kont

20/20 testów Django przeszło: 16 testów kont i 4 testy runtime.
Sprawdzono pierwsze konto bez uprawnień superuser, odrzucenie ponownej konfiguracji i słabego hasła, CSRF dla anonimowych operacji, logowanie i wylogowanie, brak informacji o istnieniu konta, użytkownika nieaktywnego, limity loginu i źródła, wygaśnięcie okna limitu, brak sekretów w logach, odzyskiwanie dostępu i unieważnienie sesji, brak tworzenia konta przy błędnym odzyskiwaniu, zgodność haseł oraz współbieżną konfigurację.
Test współbieżności wykonał dwa równoległe żądania usługowe na rzeczywistym PostgreSQL i potwierdził dokładnie jedno konto.

Migracje wygenerowane, zastosowane i sprawdzone: makemigrations --check --dry-run nie wykrywa zmian.
Testy używają osobnej bazy testowej i szybkiego hashera wyłącznie w ustawieniach testów; uruchomiona aplikacja zachowuje domyślny hasher Django.
Nie tworzono kont użytkownika w bazie lokalnej aplikacji. Pozostaje gotowa do pierwszej konfiguracji.
Interfejs logowania przewidziano w bolcie 006, a gospodarstwa i zaproszenia w boltach 003–004.
Nie mierzono procentowego pokrycia kodu ani wydajności całego produktu; pomiar P95 pozostaje w bolcie 008.
