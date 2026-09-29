# Bramka projektowania i oceny UI/UX

## Warunek rozpoczęcia implementacji

Przed implementacją każdego nowego okna UI/UX we frontendzie (ekranu, strony, dialogu lub istotnie nowego widoku) model musi wykonać kolejno: plan, wizualizację i ocenę niezależnego agenta. Dopiero jawna akceptacja tej konkretnej wersji z wynikiem **Score > 7,5/10** pozwala wdrożyć projekt w kodzie aplikacji. Wynik równy 7,5 nie spełnia warunku. Reguła obowiązuje również nowe widoki dodawane w trwającym bolcie; nie wymaga ponownego zatwierdzania historycznych, już wdrożonych ekranów.

## Plan i wizualizacja

1. Przeczytaj aktywny bolt lub task, stories, wymagania produktu oraz `design-system.md`. Sprawdź istniejące ekrany i komponenty przed zaprojektowaniem nowych.
2. Zapisz plan: cel użytkownika, zakres, układ informacji, przebieg interakcji, role, walidację oraz stany normalne, puste, ładowania, błędu i powodzenia, jeśli mają zastosowanie. Uwzględnij wersję desktopową i mobilną oraz dostępność klawiaturową.
3. Przygotuj wizualizację przed zmianami w produkcyjnym frontendzie: makietę lub odizolowany prototyp z widocznym układem, typografią, kolorami i kluczowymi stanami. Sam opis tekstowy nie jest wizualizacją. Prototyp nie może być wdrożeniem do aplikacji ani obejściem bramki.
4. Zapisz plan i wersjonowane wizualizacje w `memory-bank/bolts/<bolt-id>/evidence/ui-design/` albo `memory-bank/tasks/<task-id>/evidence/ui-design/`. Używaj syntetycznych danych. Każdy nowy widok musi mieć jednoznaczne powiązanie z ocenioną wersją.

## Niezależna ocena

1. Przekaż plan i rzeczywiste wizualizacje osobnemu agentowi recenzującemu. Agent tworzący projekt lub implementację nie może ocenić własnej pracy. Ta reguła jawnie wymaga delegowania oceny do niezależnego subagenta; nie twórz nowego czatu użytkownika.
2. Recenzent ogląda wizualizacje i ocenia w skali 0–10: użyteczność i zgodność z wymaganiami, hierarchię i czytelność, spójność z design systemem, dostępność oraz responsywność i stany interakcji. Score to średnia pięciu ocen z równymi wagami; próg sprawdzaj przed zaokrągleniem. Każdy widok oceniaj osobno, aby dobry ekran nie maskował słabego.
3. Zapisz raport obok wizualizacji: identyfikator recenzenta, datę, ocenianą wersję i ścieżki, pięć ocen z uzasadnieniem, wynik Score, problemy i decyzję `accepted` lub `changes-required`. Akceptacja wymaga Score > 7,5 oraz braku blokujących problemów użyteczności, dostępności i zgodności z wymaganiami.
4. Przy Score <= 7,5 lub decyzji `changes-required` popraw plan i wizualizację, następnie zleć ponowną niezależną ocenę. Nie podnoś wyniku samodzielnie, nie zastępuj recenzji deklaracją autora i nie rozpoczynaj implementacji, oczekując późniejszej akceptacji.
5. Jeśli niezależny agent lub narzędzie wizualizacji są niedostępne, zachowaj plan i dostępne artefakty, zgłoś blokadę i wstrzymaj implementację tego widoku. Możesz kontynuować niezależne prace, które nie omijają bramki.

## Implementacja zaakceptowanej wersji

- Przed edycją frontendu odczytaj raport i potwierdź, że akceptacja dotyczy wdrażanej wersji. W planie implementacji wskaż wizualizację, raport i Score.
- Istotna zmiana układu, nawigacji lub interakcji po akceptacji wymaga aktualizacji wizualizacji i ponownej oceny przed implementacją zmienionego zakresu.
- Po implementacji porównaj rzeczywisty ekran z zaakceptowaną wizualizacją, zweryfikuj desktop, mobile i interakcje oraz wykonaj wymagane formatowanie, kontrolę jakości i testy. Ocena makiety nie zastępuje testów aplikacji.
