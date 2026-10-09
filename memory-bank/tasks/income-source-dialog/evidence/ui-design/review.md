# Niezależna ocena projektu — income-source-dialog v2

Recenzent: `/root/review_source_dialog`. Data: 2026-10-09. Etap: przed implementacją. Decyzja: **accepted** dla obu formularzy.

Przeczytano plan v2, standard UI review i design-system.md oraz prototype.html. Rzeczywiście obejrzano wszystkie dziewięć nowych wizualizacji: desktop.jpg, mobile.jpg, contract.jpg, contract-mobile.jpg, details.jpg, error.jpg, pending.jpg, discard.jpg i company.jpg. Historyczny wynik v1 zachowano w review-v1.md. To akceptacja projektu, nie dowód poprawności wdrożenia lub pełnej zgodności WCAG.

## Inne źródło

| Kryterium | Ocena | Uzasadnienie |
| --- | ---: | --- |
| Użyteczność i wymagania | 9 | Akcja w select otwiera modal; podstawowe pola są krótkie, dodatkowe dostępne. Jeden słownik i wspólne formularze pozostają spójne z gospodarstwem. |
| Hierarchia i czytelność | 8 | Tytuł, informacja o osobnym zapisie przychodu i pojedyncza akcja są czytelne. Szczegóły mają własny poziom informacji. |
| Spójność z systemem | 8 | Jasna powierzchnia, granatowy tekst, zielone działania i obramowania zachowują motyw aplikacji. Docelowy font ma pozostać Geist z aplikacji. |
| Dostępność | 8 | Widoczne etykiety i fokus pierwszego selecta, natywny dialog oraz wymagany powrót fokusu i obsługa Escape są opisane. Pokazano tekstowy błąd i pending. |
| Responsywność i stany | 9 | Jedna kolumna przy 390 px, wewnętrzny scroll i komplet rozkładów błędu/pending/dirty. Potwierdzenie wyraźnie odróżnia szkic źródła od szkicu przychodu. |

Score = (9 + 8 + 8 + 8 + 9) / 5 = **8,4/10**. Decyzja **accepted**; brak blokujących problemów projektu.

## Umowa

| Kryterium | Ocena | Uzasadnienie |
| --- | ---: | --- |
| Użyteczność i wymagania | 9 | Pełne pola umowy i dodawanie firmy zachowane. Opcjonalny koniec i wskazówka czasu nieokreślonego odpowiadają wymaganiu. |
| Hierarchia i czytelność | 8 | Poprawiono rozciągnięte kontrolki, wyrównanie pól i odstęp przed zapisem. Większa wysokość wiersza firmy wynika z dodatkowej akcji, a nie z wysokości selecta osoby. |
| Spójność z systemem | 8 | Ten sam modal, pola i akcje co inne źródło. Firma ma mniejszy dialog w tej samej palecie. |
| Dostępność | 8 | Fokus na rodzaju źródła, czytelne etykiety i wyjaśnienie końca. Plan określa niezależny top-layer firmy i powrót fokusu. |
| Responsywność i stany | 8 | contract-mobile.jpg potwierdza pojedynczą kolumnę i ograniczenie wysokości z wewnętrznym przewijaniem. Wspólny projekt stanów dotyczy obu rodzajów. |

Score = (9 + 8 + 8 + 8 + 8) / 5 = **8,2/10**. Decyzja **accepted**; brak blokujących problemów projektu.

## Uwagi do wykonania i końcowego odbioru

- Zachować wspólne ContractForm/OtherSourceForm, istniejące endpointy i reguły. Nie tworzyć nowej encji ani automatycznego przychodu. Pusta data końca umowy ma pozostać null także w pełnym formularzu gospodarstwa.
- W rzeczywistym komunikacie błędu ukrytego pola rozwinąć szczegóły, dodać tekst przy właściwym polu i udostępnić ten błąd czytnikowi; czerwona ramka sama nie wystarcza. error.jpg przedstawia ogólną powierzchnię błędu, nie wiążący zestaw wszystkich komunikatów API.
- Preferowana drobna korekta copy w potwierdzeniu: „Wróć do formularza” zamiast kolejnego „Anuluj”. Nie zmienia to zatwierdzonego układu. Zablokować edycję/zapis starego szkicu, gdy potwierdzenie odrzucenia jest otwarte.
- company.jpg jest syntetyczną ilustracją warstw, zawiera skumulowany stan poprzedniego formularza „Inne źródło”. W aplikacji firma jest otwierana wyłącznie z umowy i dopiero poza pending. Sprawdzić to testem; nie odtwarzać skumulowanego stanu ilustracji.
- Zweryfikować Tab/Shift+Tab/Escape i powrót fokusu dla rodzica, potwierdzenia oraz dziecka. Pending blokuje zamknięcie i zmianę rodzaju. Początkowy fokus trafia na rodzaj źródła.
- Odbiór ma obejmować oba formularze 1440/390 i przewinięcie mobilnej umowy do daty końca/CTA, brak poziomego overflow oraz rzeczywisty font aplikacji. Nie traktować makiety jako testu interakcji.
- Testować zachowanie kwoty/waluty/daty/załączników przychodu po otwarciu i anulowaniu, brak sentinel w source_id, dobór nowego źródła tylko przy zgodnym odbiorcy/okresie oraz brak zapisu dla Member/Viewer i zamkniętego miesiąca.

Implementacja v2 może się rozpocząć. Wymagany osobny przegląd końcowy kodu i realnych widoków.
`nDodatkowo rzeczywiście obejrzano contract-mobile-bottom.jpg (390 × 844): wewnętrzne przewijanie udostępnia opcjonalny koniec, wskazówkę oraz CTA bez poziomego obcięcia. Wspiera akceptację mobilnej umowy.
