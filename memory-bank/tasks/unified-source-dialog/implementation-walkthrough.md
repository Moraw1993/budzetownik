# Weryfikacja dwóch wejść przy100%

Przyczyna poprawki: poprzednia realizacja ujednoliciła słownik i komponenty pól, ale zostawiła duży inline formularz TWORZENIA w rodzinie. Zgłoszenie użytkownika było zasadne, ISS-2026-002 otwarto ponownie. Zdjęcia użytkownika przy60% nie zostały użyte jako dowód ergonomii.

## Wynik implementacji

OtherSourcesPanel (tworzenie) i IncomeForm otwierają ten sam IncomeSourceCreate. Komponent zależy od Household, a nie PeriodContext; data początku miesiąca jest jedynie podpowiedzią wejścia z przychodów. Identyczne tytuły, rodzaje źródła, kolejność i układ pól, szczegóły, stopka oraz działania. Pełny inline panel rodziny jest teraz wyłącznie edycją istniejącego źródła, z dotychczasowym wersjonowaniem i archiwizacją.

Modal max920px ma trzy/dwie/jedną kolumnę zależnie od viewportu. Nagłówek i stopka są poza scrollowalnym obszarem pól. Native fieldset w tym modalu używa display:contents, aby jego anonimowy box nie wypychał stopki; HTML disabled nadal obowiązuje i jest objęty testem podczas pending. Żadnych zmian fontu globalnego, zoom/scale ani zmniejszania kontrolek. Opis ma dwa wiersze, regularność znajduje się obok opisu na desktopie.

Zapis z rodziny odświeża dane i liczniki. Nowa umowa ma komunikat wskazujący zakładkę Umowy. Zapis z przychodów zachowuje szkic i dobiera źródło wyłącznie przy zgodnym odbiorcy/okresie. Brak zmian backendu lub migracji.

## Dowody

- Makieta accepted8.2–8.5/10: evidence/ui-design/review.md.
- Dwanaście rzeczywistych JPEG: actual-family, actual-income i actual-contract przy1920x950,1440x800,1366x650,390x740. Dane syntetyczne i zoom100%; browser viewport uwzględnia paski przeglądarki monitora1920x1080.
- unified-source-dialog.spec.ts:9PASS. Cztery przypadki porównują dokładnie geometrię i etykiety obu wejść, również po rozwinięciu. Przy1920 sprawdzają brak scrolla wszystkich pól. Cztery sprawdzają końcową datę umowy i widoczność całego CTA/Anuluj. Ostatni zapisuje pełne źródło z rodziny i sprawdza słownik, brak przychodu oraz powrót fokusu.
- Na1366 automatyczny scrollIntoView pozostawiał1px obramowania textarea poza panelem; test używa teraz rzeczywistego wheel do końca. Zachowano mocne ratio1, bez obniżania asercji widoczności. Początkowe nieudane przebiegi nie są PASS.
- Pełna regresja:81PASS,2SKIP, exit0 —9plików: unified-source-dialog, income-source-dialog, periods-income, periods-recovery, periods-api, periods-render, records, family, foundation. Live pominięte z braku konfiguracji; API testów mockowane. Nie jest to nowy odbiór prawdziwego backendu.
- scripts/quality.ps1:PASS; formatter, Ruff, ESLint, Stylelint, TypeScript i probes.
- Docker frontend build:PASS; obraz sha256:9259cfcf3f703404286c7c0422501194223a5e79ea5ccd68595e338e69cc77e1. Główna aplikacja będzie aktualizowana po final review/integracji.

## Końcowa niezależna recenzja

Checkpoint8f3e2e1. Recenzent /root/review_unified_sources obejrzał wszystkie12actualJPEG i przejrzał wspólny komponent oraz oba wejścia. Accepted8.5–8.8/10, brak blockerów. Samodzielnie uruchomił16testówPASS (records8, recovery6, zapis rodziny1, ukryty błąd1). Raport: evidence/ui-design/final-review.md. Baza develop09eafea777f4fde5614f8e7d7ca0b73a91a0cdd9 ponownie pobrana i merge-tree bez konfliktów.

Historyczne obrazy poprzedniego taska zachowano. Testy zapisują nowe dowody do bieżącego taska. Pliki użytkownika ISS-2026-001 i pnpm pozostają poza zmianą. Bolt017 oraz release nie są częścią taska.
