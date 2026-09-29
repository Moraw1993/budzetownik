---
id: 003-other-sources
unit: 001-family-income-api
intent: 002-family-income-management
status: complete
priority: must
created: '2026-09-23T08:26:40Z'
assigned_bolt: 010-family-income-api
implemented: true
requirements:
  - FR-04
  - FR-05
  - FR-07
---

# Inne źródła osoby i gospodarstwa

## User Story

Jako Administrator chcę dodać inne źródło dochodu osobie lub gospodarstwu bez wypełniania pól umowy.

## Kryteria akceptacji

- [ ] Źródło `other` można zapisać dla aktywnego członka albo dla całego gospodarstwa (`member_id = null`). Członek może mieć dowolną liczbę źródeł.
- [ ] Nazwa, kategoria, daty, waluta i dotychczasowe pola źródła zachowują znaczenie, a domyślna miesięczna kwota może być pusta; podana kwota zachowuje precyzję dziesiętną.
- [ ] Źródło `other` nie ma szczegółów umowy; wybór częstotliwości „jednorazowo” nie może jednocześnie oznaczać dochodu regularnego.
- [ ] Zapis lub edycja nie tworzy przychodu miesięcznego. Lista źródeł rozróżnia `contract` i `other`, właściciela i status.
- [ ] Backend egzekwuje role, izolację gospodarstw i audyt zmian.

## Zależności

Istniejące API `income-sources/`; model źródła rozbudowany w bolcie 010.
