---
stage: model
bolt: 003-foundation-api
created: 2026-09-10T05:59:24.568Z
---
# Model domeny gospodarstw

Gospodarstwo (Household) jest granicą dostępu do danych. Ma identyfikator, nazwę, walutę domyślną PLN i czas utworzenia.
Członkostwo konta (Membership) łączy jedno konto z jednym gospodarstwem i rolą Owner, Administrator, Member lub Viewer. Nie jest osobą w rodzinie (HouseholdMember, osobny późniejszy moduł).
Para gospodarstwo–konto jest unikalna. Konto może należeć do wielu gospodarstw i mieć różne role.

## Niezmienniki agregatu
Utworzenie gospodarstwa i pierwszego członkostwa Owner jest atomowe.
Każde gospodarstwo zachowuje co najmniej jednego Owner. Zmiana ról, usunięcie dostępu i przekazanie własności są serializowane w ramach gospodarstwa.
Usunięcie członkostwa nie usuwa konta ani danych rodzinnych.
Owner zarządza dostępem; Owner i Administrator edytują dane; wszystkie cztery role odczytują dane.
Przekazanie własności istniejącemu członkostwu nadaje mu Owner i zmienia dotychczasowego właściciela na Administrator w jednej transakcji.

## Usługi i odczyty
Tworzenie gospodarstwa, zmiana nazwy, zmiana roli, odebranie dostępu, przekazanie własności.
Odczyt listy gospodarstw przez aktualne członkostwa; odczyt zasobów przez jawny identyfikator gospodarstwa.
Zdarzenia bezpieczeństwa: utworzenie, zmiana roli, odebranie dostępu, przekazanie własności; identyfikatory wykonawcy i obiektu, bez haseł i nazw finansowych.
Repozytorium: Django ORM; wspólna polityka dostępu i blokada agregatu w usługach, bez osobnej abstrakcji repozytorium.
