# Architektura systemu

Źródło: [product-requirements.md](product-requirements.md), sekcje 3–5, 54–58, 61–66.

Aplikacja full-stack: interfejs React/TypeScript, backend Django z API, PostgreSQL.
Backend jako modularny monolit. Domeny: auth, households, members, income, budgets, loans, savings, investments, analytics, attachments, audit.
Inwestycje są rozszerzeniem V2; obecność w docelowym modelu nie włącza ich do MVP.

Użytkownik może należeć do wielu gospodarstw, członek gospodarstwa może nie mieć konta.
Role są przypisane w gospodarstwie, odrębnie od relacji rodzinnych.
Każde żądanie dotyczące danych finansowych podlega kontroli dostępu w backendzie.

Budżet jest planem. Transakcje oszczędnościowe i spłaty kredytów rejestrują odrębne zdarzenia; przyszły moduł wydatków nie jest częścią MVP.
Analityka agreguje dane domenowe, zachowując rozdzielenie planu, sald i zobowiązań.
Oficjalny harmonogram bankowy może być źródłem nadrzędnym.
Załączniki: metadane w bazie, zawartość poza nią.

Szczegółowe kontrakty API, model sesji, granice transakcji i schemat bazy będą opracowane w planowaniu i projektowaniu.

## Wdrożenie MVP
Lokalny Docker Compose na komputerze użytkownika: usługi frontendu, Django i PostgreSQL. Dostęp z przeglądarki przez localhost; porty aplikacji wiązane z 127.0.0.1. Baza w sieci wewnętrznej kontenerów; baza i załączniki na trwałych wolumenach. Szczegóły w ../operations/local-deployment.md.
