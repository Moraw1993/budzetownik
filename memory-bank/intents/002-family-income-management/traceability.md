# Pokrycie wymagań

| Wymaganie | Właściciel | Stories | Bolt |
| --- | --- | --- | --- |
| FR-01 Zarządzanie rodziną | UI | [Nawigacja](units/002-family-management-ui/stories/001-family-navigation.md) | [011](../../bolts/011-family-management-ui/bolt.md) |
| FR-02 Firma | API | [Słownik](units/001-family-income-api/stories/001-company-dictionary.md), [Formularz](units/002-family-management-ui/stories/002-contract-company-forms.md) | [010](../../bolts/010-family-income-api/bolt.md), [011](../../bolts/011-family-management-ui/bolt.md) |
| FR-03 Umowa | API | [Źródło umowne](units/001-family-income-api/stories/002-contract-sources.md), [Formularz](units/002-family-management-ui/stories/002-contract-company-forms.md) | 010, 011 |
| FR-04 Inne źródło | API | [Źródło](units/001-family-income-api/stories/003-other-sources.md), [Formularz](units/002-family-management-ui/stories/003-other-source-and-conversion.md) | 010, 011 |
| FR-05 Bez miesięcznego przychodu | API | [Umowa](units/001-family-income-api/stories/002-contract-sources.md), [Inne źródło](units/001-family-income-api/stories/003-other-sources.md), [Odbiór](units/003-family-income-acceptance/stories/002-family-user-journey.md) | 010, 012 |
| FR-06 Migracja i historia | API | [Migracja](units/001-family-income-api/stories/004-legacy-source-migration.md), [Konwersja UI](units/002-family-management-ui/stories/003-other-source-and-conversion.md), [Odbiór](units/003-family-income-acceptance/stories/001-migration-and-isolation.md) | 010, 011, 012 |
| FR-07 Role i izolacja | API | [Słownik](units/001-family-income-api/stories/001-company-dictionary.md), [Umowa](units/001-family-income-api/stories/002-contract-sources.md), [Inne źródło](units/001-family-income-api/stories/003-other-sources.md), [Odbiór](units/003-family-income-acceptance/stories/001-migration-and-isolation.md) | 010, 012 |
| NFR-01 Bezpieczna migracja | API i odbiór | [Migracja](units/001-family-income-api/stories/004-legacy-source-migration.md), [Odbiór](units/003-family-income-acceptance/stories/001-migration-and-isolation.md) | 010, 012 |
| NFR-02 Jednoznaczność kwot | UI i odbiór | [Umowa UI](units/002-family-management-ui/stories/002-contract-company-forms.md), [Inne źródło UI](units/002-family-management-ui/stories/003-other-source-and-conversion.md), [Odbiór](units/003-family-income-acceptance/stories/002-family-user-journey.md) | 011, 012 |
| NFR-03 Zgodność przejściowa | API | [Migracja](units/001-family-income-api/stories/004-legacy-source-migration.md) | 010 |

Wszystkie FR mają jednego właściciela reguły wskazanego w [podziale jednostek](units.md). Dodatkowe stories UI i odbioru nie przenoszą tych reguł z backendu.
