---
stage: test
bolt: 001-local-runtime
created: 2026-09-10T05:46:12.392Z
---
# Testy runtime

- Django check: bez błędów.
- 4/4 testy gotowości: zdrowa baza, błąd bazy bez ujawniania szczegółów, oczekujące migracje, odrzucenie POST.
- Zbudowano produkcyjny frontend z kontrolą TypeScript.
- Test HTTPS zweryfikował certyfikat przez wyeksportowany CA, bez importu do Windows.
- Rekord testowy i plik przetrwały odtworzenie kontenerów.
- Wyłączenie bazy powoduje 503; po uruchomieniu baza wraca do gotowości.
- Ponowna konfiguracja zachowuje .env; brak hasła powoduje czytelny błąd.
- Prettier, ESLint, Stylelint, Ruff i TypeScript: wynik poprawny po poprawkach formatowania.

Pierwszy test awarii bazy miał za krótki timeout względem DNS Dockera; zwiększono timeout testu do 20 s i ponowne wykonanie przeszło.
curl Windows zgłaszał niedostępność danych o odwołaniu lokalnego certyfikatu; Python zweryfikował podpis i host przez jawny CA.
Nie wykonano importu CA do Windows. Nie ma jeszcze logowania, domen gospodarstwa ani pełnego backup/restore z bolta 008.
