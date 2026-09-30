---
environment: staging
verified: 2026-09-30T08:10:34Z
status: passed
---

# Odbiór stagingu d670985

- Odtworzone API obu gospodarstw i wszystkie 9 tabel domenowych dokładnie zgodne ze snapshotami dev przed testami zapisu.
- Baza/backend/frontend healthy, migrate exit 0, Caddy działa; backend/frontend RestartCount=0. `/api/health/` sprawdza bazę i migracje. Brak osobnego `/ready`, cache i integracji zewnętrznych w tym runtime.
- HTTPS: Owner tworzy firmę, edytuje, archiwizuje i odczytuje. Pusta nazwa zwraca 400. Administrator/Member/Viewer odczytują własne gospodarstwo; obce jest odrzucane. Member/Viewer nie mogą tworzyć firmy.
- Edge: logowanie, wybór gospodarstwa, zakładki Członkowie/Umowy/Źródła dochodu. Zrzuty 1440×1000 i 390×844; brak poziomego przepełnienia dokumentu.
- Ruff format/check i scripts/quality.ps1 przeszły bez wyłączania reguł.

## Pomiar

HTTPS localhost z zaufanym CA target, Owner, jedno trwałe połączenie, współbieżność 1, 10 rozgrzewek i 100 próbek na operację, P95 nearest rank. Dane z odbioru rodziny 012.

| Odczyt | P95 | Błędy / próbki |
| --- | --- | --- |
| Gospodarstwa | 8,94 ms | 0/100 |
| Członkowie | 6,69 ms | 0/100 |
| Źródła | 7,84 ms | 0/100 |

Cel P95 <500 ms spełniony w tym zakresie. Próbka docker stats: CPU 0–3,35%, pamięć 0,10–0,66% zasobów Docker. To nie jest test obciążeniowy ani pomiar zapisów, długoterminowej dostępności lub monitoringu. Brak poprzedniej wersji stagingu do porównania.

## Dowody i ograniczenia

Lokalnie `.runtime/acceptance/17d4acaa/`: staging-verification.json, staging-contracts.png, staging-sources.png, staging-mobile.png, backup/ i snapshoty 012. Sekrety poza Git.

Narzędzie verify_family_staging.py wymaga czystego restore przed ponownym uruchomieniem: porównuje dane, potem celowo zapisuje testową firmę i audyt. Wstępna próba ujawniła złą nazwę roli w narzędziu; poprawiono i ponowiono od czystej kopii. Przeglądarkę i selektory dostosowano do Edge i faktycznych nazw zakładek; końcowy odbiór przeszedł. Produkt nie wymagał zmian.

Pełne E2E zapisu umów 5/5 wykonano wcześniej w dev, nie ponawiano ich na target. Produkcja i monitoring pozostają otwarte.
