# Evidence

Inspekcja źródeł: frontend/app/components/income-form.tsx (CTA i panel), income-source-create.tsx (wspólne formularze), contract-form.tsx (end_date bez required, null w payload), other-source-form.tsx, backend/households/record_serializers.py (allow_null, required=False) i models.py (null=True, blank=True).

Dowody wizualne i testowe naprawy: ../../../tasks/income-source-dialog/evidence/ui-design/.
