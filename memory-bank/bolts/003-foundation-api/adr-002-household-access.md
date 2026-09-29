---
status: accepted
created: 2026-09-10T05:59:24.568Z
bolt: 003-foundation-api
---
# ADR-002: Jawny zakres gospodarstwa i blokada zmian dostępu

Kontekst: użytkownik może mieć różne role w wielu gospodarstwach. Dwa równoległe zapisy nie mogą usunąć ostatniego Owner.

Decyzja: zakres jest częścią URL, kontrolowany przez aktualne członkostwo w bazie. Usługi zapisujące agregat blokują jego wiersz i dopiero potem sprawdzają rolę. Zmiany właścicieli używają jednej transakcji. Polityka dostępu jest współdzielona przez kolejne domeny.

Konsekwencje: prosty model dla lokalnego MVP i jednoznaczny kontekst kart przeglądarki; zapisy jednego gospodarstwa czekają na siebie. Bezpośrednie operacje ORM operatora omijają usługi i nie są wspieranym interfejsem zarządzania rolami. Nie udostępniamy usuwania kont ani gospodarstw. Każdy przyszły zapis członkostwa musi stosować tę samą blokadę.
