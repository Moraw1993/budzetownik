# Propozycja monitoringu lokalnego MVP

Status: plan do checkpointu 4; nie wdrożono konfiguracji monitoringu.

Zakres proponowany dla lokalnej instalacji: zachować aktualne healthchecki bazy/backendu/frontendu, ustawić ograniczoną rotację logów Docker (max-size 10m, max-file 3) dla usług tego projektu oraz przygotować instrukcje reakcji na niedostępność, powtarzające się restarty i błędy migracji. Sprawdzać aktualne obrazy, health, restarty i chwilowe zużycie zasobów bez logowania sekretów lub prywatnych rekordów.

Rotacja wymaga odtworzenia kontenerów; konfigurację należy sprawdzić najpierw na stagingu i po akceptacji wdrożyć do prywatnej instalacji z zachowaniem danych. Plan nie zmienia portów, bazy, certyfikatów ani nie dodaje usług zewnętrznych. Nie tworzy automatyzacji cyklicznej, nie wysyła email/Slack i nie instaluje agentów systemowych.

Ten ograniczony zakres nie daje ciągłych metryk RED, dashboardu ani potwierdzenia SLO 99,9%. Jeśli użytkownik wybierze go zamiast pełnej platformy obserwowalności, końcowy raport musi jawnie oznaczyć te elementy jako odroczone. Pełne dashboardy i automatyczne alerty wymagają osobnego uzgodnienia stosu i kanału powiadomień; przykładowe cele ze skilla nie są automatycznie wymaganiami tego lokalnego MVP.
