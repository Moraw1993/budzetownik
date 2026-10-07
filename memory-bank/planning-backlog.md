---
created: 2026-09-30T09:41:32Z
updated: 2026-09-30T09:41:32Z
status: proposed
---

# Backlog przyszłych intentów

Dokument utrzymuje agent specsmd Inception. Wpisy są materiałem do przyszłego planowania; nie oznaczają ukończonego Inception, zatwierdzonego projektu UI ani rozpoczęcia Construction. Identyfikatory intentów i boltów nadać dopiero przy formalnym planowaniu, po sprawdzeniu dostępnej numeracji.

## Profil członka rodziny i historia finansowa

**Źródło:** propozycja użytkownika z 2026-09-30, następnie polecenie zapisania uzgodnionej koncepcji w dokumentacji. **Termin:** przyszły intent po wdrożeniu lat, miesięcy budżetowych i rzeczywistych przychodów. Nie rozszerza zakończonego intentu [002-family-income-management](intents/002-family-income-management/requirements.md) ani bolta 012.

### Cel i kierunek

Karta członka pozostaje skrótem na liście rodziny. Kliknięcie imienia lub jawnej akcji „Otwórz profil” prowadzi do osobnej podstrony konkretnej osoby, z możliwością powrotu do listy. Profil ma własny adres w kontekście gospodarstwa; wejście bezpośrednio pod adres również wymaga autoryzacji. „Edytuj” pozostaje odrębną akcją.

### Proponowany zakres

- Podsumowanie: dane członka, relacja, status, opcjonalnie powiązane konto i aktywne źródła dochodu. Członek bez konta ma pełnoprawny profil.
- Umowy: wszystkie umowy tej osoby, aktywne i zakończone; firma, daty, warunki i historia zmian. Rozdzielić historię zapisów od historii okresów obowiązywania; sposób rekonstrukcji dawnych warunków wymaga decyzji podczas Inception.
- Źródła dochodu: źródła przypisane tej osobie, również archiwalne. Źródła całego gospodarstwa nie są automatycznie przypisywane członkowi.
- Przychody: rzeczywiście zapisane wpływy tej osoby, filtry rok/miesiąc/źródło i odnośniki do odpowiedniego miesiąca. Kwoty brutto umów i podpowiedzi źródeł nie są przychodami. Przy wielu walutach nie sumować ich bez uzgodnionej reguły przeliczenia.
- Historia: istotne zmiany danych członka, umów i źródeł, z datą i wykonawcą w granicach uprawnień. Nie deklarować istniejącego audytu jako gotowego, kompletnego wersjonowania umów.

### Granice i zależności

Dodawanie oraz edycja przychodów pozostają częścią karty miesiąca i jej reguł statusu. Profil korzysta z tych samych rekordów, bez drugiej ewidencji. Pełne zestawienia rodziny, źródeł i umów nadal służą do przeglądu całego gospodarstwa.

Izolację gospodarstw i role sprawdza backend. Punktem wyjścia są istniejące role Owner/Administrator do edycji oraz Member/Viewer do odczytu; ewentualne ograniczenie widoczności finansów poszczególnych osób jest otwartą decyzją, nie wprowadzonym uprawnieniem.

### Wymagania do uwzględnienia już przy planowaniu przychodów

Zmiana nazw, warunków umowy, przypisania źródła lub archiwizacja osoby/źródła nie może przepisywać historycznych przychodów ani przypisywać dawnych wpływów innej osobie. W modelu przychodu określić stabilne przypisanie gospodarstwa i członka oraz dane historyczne utrwalane przy zapisie. Rozważyć snapshot albo wersjonowane odniesienie; konkretną strategię wybrać w projekcie domeny.

Zapewnić zapytania i indeksy do filtrowania przychodów według gospodarstwa, członka, okresu i źródła. Profil później wykorzysta ten model, zamiast migrować historię na podstawie aktualnych powiązań.

### Następne kroki formalnego Inception

1. Zaplanować lata/miesiące i przychody, uwzględniając powyższą trwałość historii.
2. Utworzyć osobny intent profilu i doprecyzować widoczność danych, zakres historii umów, akcje i waluty.
3. Przygotować wymagania, kontekst, jednostki, stories oraz bolty przez checkpointy specsmd. Nie rezerwować numeru ani terminu w tym wpisie.
4. Przed implementacją nowej podstrony wykonać plan, wizualizację i niezależną ocenę oraz uzyskać jawną akceptację z Score >7,5 zgodnie z [bramką UI](standards/ui-design-review.md). Zaplanować odbiór pustego profilu, archiwalnego członka, wielu umów, różnych walut, mobile i klawiatury.
