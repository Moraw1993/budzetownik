---
stage: model
bolt: 002-foundation-api
created: 2026-09-10T05:46:12.392Z
---
# Model kont i sesji

## Encje i agregaty
User jest kontem logowania, niezależnym od HouseholdMember. Posiada identyfikator, unikalny login, skrót hasła i stan aktywności.
Stan konfiguracji początkowej: istnieje co najmniej jeden użytkownik → konfiguracja zamknięta. Transakcyjna blokada serializuje tworzenie pierwszego konta.
Session przechowuje uwierzytelnienie powiązane z kontem; nie przechowuje hasła.
LoginThrottle przechowuje licznik prób w oknie czasowym dla skrótu klucza loginu i źródła żądania.

## Niezmienniki
Pierwsze konto tworzy się dokładnie raz; brak automatycznych uprawnień superuser/staff.
Kolejne konta wyłącznie w zaproszeniach (bolt 004).
Wylogowanie i zmiana hasła odbierają dostęp wcześniejszym sesjom.
Nieprawidłowe dane oraz nieistniejące konto dają taki sam błąd logowania.
Nie wolno zapisywać haseł, sesji ani tokenów w logach.

## Usługi i zdarzenia
BootstrapAccount: atomowe sprawdzenie stanu, walidacja i utworzenie konta.
Login: walidacja, rezerwacja próby, uwierzytelnienie i utworzenie sesji.
Recovery: lokalny operator zmienia hasło istniejącego konta.
Zdarzenia: konto utworzone, udane/nieudane logowanie, wylogowanie, zmiana hasła; logowane bez sekretów.

## Granice
Role gospodarstwa i zaproszenia powstają w kolejnych boltach.
ORM Django obsługuje repozytorium User, sesje i liczniki. Nie dodajemy abstrakcyjnej warstwy repozytorium bez potrzeby.
