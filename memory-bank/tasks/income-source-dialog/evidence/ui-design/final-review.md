# Niezależny odbiór implementacji — income-source-dialog v2

Recenzent: `/root/review_source_dialog`. Data: 2026-10-09. Baza przeglądu: develop `63df3c6`, branch `fix/task-income-source-dialog`. Decyzja: **accepted**. Nie stwierdzono blokujących błędów P1/P2.

## Zakres i dowody niezależne

Przejrzano diff sześciu plików produkcyjnego UI: contract-form.tsx, income-form.tsx, income-source-create.tsx, other-source-form.tsx, ui.tsx i globals.css, nowy income-source-dialog.spec.ts oraz zmiany periods-recovery.spec.ts/periods-live.spec.ts. Odczytano również istniejące CompanyDialog, ConfirmAction i ActionForm, żeby sprawdzić rzeczywistą obsługę fokusu i pending.

Rzeczywiście obejrzano actual-other-1440.jpg, actual-other-390.jpg, actual-contract-1440.jpg i actual-contract-390.jpg. Potwierdzają nowy modal w obecnym shellu, wyrównane kontrolki, jedną kolumnę i wewnętrzny scroll na 390 px oraz widoczny koniec umowy i CTA po przewinięciu.

Recenzent niezależnie uruchomił na lokalnym podglądzie 8098 pięć testów income-source-dialog.spec.ts i sześć testów periods-recovery.spec.ts: **11/11 PASS**. Osobne katalogi wyników `.runtime/review-source-dialog-unsandboxed` oraz `.runtime/review-source-recovery`. Pierwsza próba w sandboxie nie uruchomiła Edge (błąd uprawnień procesu); powtórzenie z wymaganym dostępem zakończyło się PASS. Nie jest to awaria produktu.

Niezależnie zweryfikowane scenariusze obejmują: początkowy i przywracany fokus, modalność klawiaturową, szkic kwoty/daty/pliku, sentinel niewchodzący do wartości źródła, Escape przy pristine i dirty, inert podczas potwierdzenia, zagnieżdżony dialog firmy i powrót do selecta firmy, pusty end_date wysyłany jako null, opis dostępny end_date, brak automatycznego przychodu, odsłonięcie tekstowego błędu pola w szczegółach oraz zablokowane zamknięcie przez Escape podczas pending. Recovery obejmuje także utratę roli, nieznany wynik i konflikty.

Autor przekazał wynik pełnego przebiegu: 72 PASS / 2 SKIP, quality.ps1 PASS i finalny Docker frontend build PASS. Tych szerokich przebiegów recenzent nie powtarzał; nie należy mylić ich z niezależnym powtórzeniem 11 scenariuszy. Dwa SKIP dotyczą live bez danych instalacji testowej. Testy tego taska korzystają z mockowanego API, nie stanowią nowego testu end-to-end prawdziwego backendu.

## Ocena wdrożonych widoków

| Kryterium | Inne źródło | Umowa | Uzasadnienie |
| --- | ---: | ---: | --- |
| Użyteczność i wymagania | 9 | 9 | Akcja w select, modal oraz wspólny słownik i formularze; umowa nie wymaga daty końca. |
| Hierarchia i czytelność | 8 | 8 | Prosty podstawowy formularz, opcjonalne szczegóły, jeden zapis; umowa pozostaje dłuższa ze względu na domenę. |
| Spójność z systemem | 9 | 9 | Realny shell, font i tokeny aplikacji; wyrównanie kontrolek zgodne z projektem v2. |
| Dostępność | 9 | 8 | Fokus, natywny top-layer, inert i pending potwierdzone testami; zagnieżdżenie umowy wymaga zachowania obecnej struktury i końcowych testów. |
| Responsywność i stany | 8 | 8 | Brak poziomego overflow przy 390, wewnętrzny scroll, tekstowe błędy i ochrona szkiców. |

Inne źródło Score = (9 + 8 + 9 + 9 + 8) / 5 = **8,6/10**, **accepted**.

Umowa Score = (9 + 8 + 9 + 8 + 8) / 5 = **8,4/10**, **accepted**.

## Wnioski techniczne i uwagi

- Zastosowano istniejące ContractForm/OtherSourceForm oraz istniejące endpointy; nie dodano nowego modelu przychodu. Compact mode reorganizuje wspólne pola bez kopiowania logiki payloadu. Pełny formularz zarządzania gospodarstwem nadal ma swoje sekcje.
- Field hint wykorzystuje aria-describedby wraz z błędem. Data końca umowy nadal nie ma required; test wysłanego payloadu potwierdza null.
- showModal zapewnia top-layer i blokuje tło, a po odrzuceniu źródła nie zmienia się szkic przychodu. ConfirmAction jest istniejącym komponentem; inert chroni stary formularz podczas potwierdzenia. CompanyDialog pozostaje niezależnym dzieckiem z własnym pending i powrotem fokusu.
- Akcja select jest dostępna zgodnie z rolą, a blokada całego formularza działa przy utracie dostępu. Backend pozostaje odpowiedzialny za autoryzację.
- Nieblokująca sugestia copy z review projektu pozostaje: „Wróć do formularza” byłoby czytelniejsze od „Anuluj” w potwierdzeniu odrzucenia. Obecny kontekst i osobna akcja „Odrzuć szkic źródła” wystarczają do odbioru.
- Użyte kontrolowane open na details odsłania błędy opcjonalnych pól. Warstwa błędów ma istniejącą tekstową prezentację i zachowuje wartości.

Akceptacja dotyczy tego taska i jego projektu v2. Można wykonać scoped commit oraz zintegrować do develop z autoryzacji użytkownika. Przed zakończeniem integracji sprawdzić aktualne referencje, konflikty i główny lokalny build. Nie obejmować commitem zachowanych plików użytkownika ani traktować tego odbioru jako release lub zamknięcia bolta017.
