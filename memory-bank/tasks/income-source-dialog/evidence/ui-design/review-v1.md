# Niezależna ocena projektu — income-source-dialog v1

Recenzent: `/root/review_source_dialog`. Data: 2026-10-09. Etap: przed implementacją. Decyzja: **changes-required**.

Przeczytano implementation-plan.md, standard UI review i design-system.md oraz prototype.html. Rzeczywiście obejrzano desktop.jpg, mobile.jpg, contract.jpg i details.jpg w tym katalogu. Ocena dotyczy wyłącznie tej wersji; nie ocenia wdrożonego kodu ani testów.

## Inne źródło

| Kryterium | Ocena | Uzasadnienie |
| --- | ---: | --- |
| Użyteczność i wymagania | 9 | Akcja w słowniku oraz centralny modal odpowiadają prośbie. Sześć pól i rozwijane szczegóły skracają podstawową ścieżkę; istniejące formularze i endpointy zachowują domenę. |
| Hierarchia i czytelność | 8 | Wyraźny tytuł i pojedynczy zapis; szczegóły oddzielone. Nagłówek mobilny zabiera więcej miejsca, ale nie blokuje obsługi. |
| Spójność | 8 | Jasna powierzchnia, granatowy tekst i zielone CTA odpowiadają systemowi. Prototyp ma Arial zamiast docelowego Geist, więc końcowa kontrola ma użyć fontu aplikacji. |
| Dostępność | 8 | Widoczne etykiety, 44 px pola, natywny modal i fokus. Wizualizacja pokazuje początkowy fokus na Anuluj, zamiast pierwszego pola wymaganego standardem. |
| Responsywność i stany | 7 | Jedna kolumna przy 390 px jest czytelna. Brakuje rzeczywistej wizualizacji pending, błędu ukrytego pola i potwierdzenia odrzucenia szkicu. |

Score = (9 + 8 + 8 + 8 + 7) / 5 = **8,0/10**. Próg liczbowy osiągnięty, ale decyzja **changes-required** ze względu na opisane braki dowodów kluczowych stanów.

## Umowa

| Kryterium | Ocena | Uzasadnienie |
| --- | ---: | --- |
| Użyteczność i wymagania | 9 | Pełna umowa i możliwość dodania firmy zachowane. Opcjonalny koniec i wyjaśnienie czasu nieokreślonego są poprawne. |
| Hierarchia i czytelność | 7 | contract.jpg pokazuje rozciągnięty select osoby oraz rozciągnięte pole początku; przycisk zapisu dotyka dolnego pola. To odtwarza problem nierównych pól zamiast prezentować poprawny układ. |
| Spójność | 8 | Kolory i powierzchnie wspólne z aplikacją; obowiązuje uwaga o foncie. |
| Dostępność | 7 | Etykiety i wskazówka końca są czytelne, lecz fokus początkowy niezgodny ze standardem; brak dowodu projektu obsługi klawiatury w zagnieżdżonym modalu firmy. |
| Responsywność i stany | 6 | Nie przedstawiono mobilnej umowy ani zagnieżdżonego modala firmy oraz stanów błędów/pending. Sam desktop nie wystarcza do oceny długiego formularza. |

Score = (9 + 7 + 8 + 7 + 6) / 5 = **7,4/10**. Decyzja **changes-required**.

## Poprawki konieczne przed kodem

1. Poprawić układ makiety umowy: pola muszą zachować jednakową wysokość kontrolek pomimo przycisku firmy i podpowiedzi końca; dodać odstęp przed CTA. Użyć istniejącego wzorca `.company-select-field`, jeśli odpowiada za ten problem w aplikacji, zamiast utrwalać rozciąganie na makiecie. Pokazać umowę również przy 390 px z przewijaniem wewnątrz modala.
2. Uzupełnić prototyp/wizualizacje o tekstowy błąd pola w rozwiniętych szczegółach, pending ze zablokowanym zamknięciem, potwierdzenie odrzucenia szkicu oraz otwarty modal firmy nad umową. W planie role i zachowanie błędów są opisane poprawnie; ich kluczowy układ musi być widoczny przed implementacją.
3. Sprecyzować i pokazać początkowy fokus na polu rodzaju/odbiorcy, nie na Anuluj; zamknięcie dziecka przywraca fokus na firmę, zamknięcie rodzica na select źródła. Potwierdzenie ma dwie jednoznaczne akcje „Wróć do formularza” i „Odrzuć szkic”, aby „Anuluj” nie miało dwóch znaczeń.

## Wymagania do odbioru implementacji

Bez nowych encji ani kopii reguł: użyć ContractForm/OtherSourceForm. Zweryfikować brak automatycznego przychodu, sentinel nie trafia do source_id, szkic przychodu i pliki pozostają bez zmian. Testować Escape/Tab/Shift+Tab i powrót fokusu, dirty przy zmianie rodzaju i zamykaniu, pending, błędy ukrytych pól, nested company modal oraz brak akcji dla Member/Viewer i zamkniętego miesiąca. Data końca pustej umowy ma wysyłać null także w pełnym formularzu gospodarstwa.

Nie rozpocząć implementacji nowych dialogów na podstawie tej wersji. Po aktualizacji planu i dowodów konieczna ponowna niezależna ocena.
