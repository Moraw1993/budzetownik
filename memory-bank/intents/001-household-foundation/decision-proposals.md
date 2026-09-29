# Decyzje dotyczące fundamentu

Status: Q-01, Q-02 oraz zakres i przedstawione doprecyzowania zatwierdzone przez użytkownika. Szczegóły projektowe oznaczone poniżej pozostają częścią przeglądu planu.

## Dostęp do kont
Pierwsze konto tworzone podczas lokalnej konfiguracji. Owner zaprasza kolejne osoby za pomocą jednorazowego linku, który można skopiować; MVP nie wymaga dostawcy poczty.
Link otwiera się na tym samym komputerze, ponieważ aplikacja jest dostępna przez localhost. Link localhost nie daje zdalnego dostępu z urządzenia zaproszonej osoby.
Uzgodnienie: zaproszenie posiada rolę i ważność 7 dni oraz możliwość odwołania; przyjęcie jest jednorazowe.
Odzyskiwanie dostępu w lokalnym MVP: przez operatora instalacji, bez wysyłania wiadomości e-mail. Procedura musi być opisana przed odbiorem.

## Zatwierdzona macierz uprawnień
| Operacja | Owner | Administrator | Member | Viewer |
|---|---|---|---|---|
| Odczyt członków i źródeł | Tak | Tak | Tak | Tak |
| Edycja członków i relacji | Tak | Tak | Nie | Nie |
| Edycja źródeł dochodu | Tak | Tak | Nie | Nie |
| Zapraszanie kont i zmiana ról | Tak | Nie | Nie | Nie |
| Przekazanie własności gospodarstwa | Tak | Nie | Nie | Nie |

Uzgodnienie: utrzymywać co najmniej jednego Owner; przekazanie roli jest atomowe i nie usuwa poprzedniemu właścicielowi konta. Rola Owner gospodarstwa jest niezależna od technicznego administratora Django.

## Pozostałe doprecyzowania
- Szczegół projektowy do przeglądu planu: konto użytkownika może być powiązane co najwyżej z jednym członkiem w danym gospodarstwie; w innym gospodarstwie ma odrębne powiązanie.
- Typy relacji rodzinnych definiowane w obrębie gospodarstwa.
- Interfejs MVP po polsku, zoptymalizowany dla desktopu i responsywny.
- Frontend: preferowany w PRD Next.js; wybór biblioteki API Django, narzędzi jakości, wersji i lokalnego HTTPS w projekcie technicznym.
