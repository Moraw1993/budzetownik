# Technologie projektu

## Źródło
Wymagania i preferencje użytkownika: [product-requirements.md](product-requirements.md), sekcje 54–57. Dokumentacja AI-DLC nie zastępuje PRD.

## Języki i framework
Backend: Python, Django. Warstwa danych: Django ORM i wbudowane migracje Django. API: Django REST Framework 3.18.1. Django 5.2.17, Python 3.13, PostgreSQL 17.
Frontend: TypeScript 5.9.3, React 19.3.0, Next.js 16.3.4 na Node 22.
UI: Tailwind CSS, shadcn/ui, Lucide Icons. Wybór Recharts lub Apache ECharts pozostaje otwarty.

## Uwierzytelnianie
Konta użytkowników i role Owner, Administrator, Member, Viewer w obrębie gospodarstwa.
Wymagane: bezpieczne haszowanie haseł, sesje, limity prób logowania, HTTPS i zabezpieczenia CSRF/XSS odpowiednie do mechanizmu logowania.
MFA/TOTP opcjonalne. Sesje Django w PostgreSQL, Secure/HttpOnly/SameSite, jawne CSRF dla logowania i konfiguracji. Odzyskiwanie hasła lokalnym poleceniem recover_account.

## Infrastruktura
MVP lokalnie na komputerze użytkownika, przez Docker Compose: frontend, Django i PostgreSQL. Dostęp przez localhost, porty aplikacji wiązane z 127.0.0.1; PostgreSQL w wewnętrznej sieci kontenerów. Baza i załączniki na trwałych wolumenach. Załączniki MVP w filesystemie, docelowo możliwy storage zgodny z S3. Szczegóły: ../operations/local-deployment.md.
Nie wybrano dostawcy ani płatnych usług.

## Zarządzanie zależnościami
Frontend: npm i package-lock.json; backend: pip i przypięte wersje w requirements.txt. Narzędzia jakości: Prettier, ESLint, Stylelint i Ruff 0.16.6.

Lokalny adres: https://localhost:8443; Caddy z wewnętrznym CA. Instrukcja eksportu i zaufania certyfikatu znajduje się w README.md.
