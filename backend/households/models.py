import calendar
import uuid
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Role(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMINISTRATOR = "administrator", "Administrator"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class Household(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    currency = models.CharField(max_length=3, default="PLN")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class Membership(models.Model):
    """Account access; a family member will be a separate entity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["household", "user"], name="unique_household_user"),
            models.CheckConstraint(
                condition=models.Q(role__in=Role.values), name="valid_household_role"
            ),
        ]


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="invitations")
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="issued_invitations"
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="accepted_invitations",
        blank=True,
        null=True,
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["household", "created_at"], name="households__househ_84f440_idx")
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=Role.values), name="valid_invitation_role"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(accepted_at__isnull=True, accepted_by__isnull=True)
                    | models.Q(accepted_at__isnull=False, accepted_by__isnull=False)
                ),
                name="invitation_acceptance_fields_match",
            ),
        ]


class ArchivableRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(is_active=True, deactivated_at__isnull=True)
                    | models.Q(is_active=False, deactivated_at__isnull=False)
                ),
                name="%(class)s_archive_state",
            )
        ]


class RelationType(ArchivableRecord):
    household = models.ForeignKey(Household, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)

    class Meta(ArchivableRecord.Meta):
        abstract = False
        constraints = [
            *ArchivableRecord.Meta.constraints,
            models.UniqueConstraint(
                fields=["household", "name"],
                condition=models.Q(is_active=True),
                name="unique_active_relation_name",
            ),
        ]


class HouseholdMember(ArchivableRecord):
    household = models.ForeignKey(Household, on_delete=models.PROTECT)
    display_name = models.CharField(max_length=180)
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    relation_type = models.ForeignKey(RelationType, on_delete=models.PROTECT, null=True, blank=True)

    class Meta(ArchivableRecord.Meta):
        abstract = False
        constraints = [
            *ArchivableRecord.Meta.constraints,
            models.UniqueConstraint(
                fields=["household", "account"], name="unique_household_member_account"
            ),
        ]


class IncomeFrequency(models.TextChoices):
    MONTHLY = "monthly", "Miesięcznie"
    WEEKLY = "weekly", "Tygodniowo"
    QUARTERLY = "quarterly", "Kwartalnie"
    YEARLY = "yearly", "Rocznie"
    ONE_OFF = "one_off", "Jednorazowo"
    IRREGULAR = "irregular", "Nieregularnie"


class IncomeKind(models.TextChoices):
    OTHER = "other", "Inne źródło"
    CONTRACT = "contract", "Umowa"


class Company(ArchivableRecord):
    household = models.ForeignKey(Household, on_delete=models.PROTECT)
    name = models.CharField(max_length=180)

    class Meta(ArchivableRecord.Meta):
        abstract = False
        indexes = [models.Index(fields=["household", "is_active", "name"])]


class IncomeSource(ArchivableRecord):
    household = models.ForeignKey(Household, on_delete=models.PROTECT)
    member = models.ForeignKey(
        HouseholdMember,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="income_sources",
    )
    name = models.CharField(max_length=180)
    kind = models.CharField(max_length=20, choices=IncomeKind.choices, default=IncomeKind.OTHER)
    version = models.PositiveIntegerField(default=1)
    category = models.CharField(max_length=100, blank=True)
    payer = models.CharField(max_length=180, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    default_monthly_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    currency = models.CharField(max_length=3, validators=[RegexValidator(r"^[A-Z]{3}$")])
    frequency = models.CharField(max_length=20, choices=IncomeFrequency.choices, blank=True)
    is_regular = models.BooleanField(default=True, null=True, blank=True)
    description = models.TextField(blank=True, max_length=2000)

    class Meta(ArchivableRecord.Meta):
        abstract = False
        indexes = [models.Index(fields=["household", "kind"], name="income_household_kind_idx")]
        constraints = [
            *ArchivableRecord.Meta.constraints,
            models.CheckConstraint(
                condition=models.Q(default_monthly_amount__gte=0), name="income_nonnegative_amount"
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="income_date_order",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(kind=IncomeKind.OTHER, frequency__in=IncomeFrequency.values)
                    | models.Q(kind=IncomeKind.CONTRACT, frequency="")
                ),
                name="income_valid_frequency",
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=IncomeKind.values), name="income_valid_kind"
            ),
            models.CheckConstraint(condition=models.Q(version__gte=1), name="income_valid_version"),
            models.CheckConstraint(
                condition=(
                    models.Q(kind=IncomeKind.OTHER)
                    | models.Q(
                        kind=IncomeKind.CONTRACT,
                        member__isnull=False,
                        category="",
                        payer="",
                        default_monthly_amount__isnull=True,
                        frequency="",
                        is_regular__isnull=True,
                        description="",
                    )
                ),
                name="income_contract_fields_clear",
            ),
        ]


class ContractType(models.TextChoices):
    EMPLOYMENT = "employment", "Umowa o pracę"
    MANDATE = "mandate", "Umowa zlecenie"
    SPECIFIC_WORK = "specific_work", "Umowa o dzieło"
    OTHER = "other", "Inna umowa"


class GrossBasis(models.TextChoices):
    MONTHLY = "monthly", "Miesięcznie"
    HOURLY = "hourly", "Godzinowo"
    TOTAL = "total", "Za całość"


class Contract(models.Model):
    source = models.OneToOneField(
        IncomeSource, on_delete=models.PROTECT, primary_key=True, related_name="contract"
    )
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    contract_type = models.CharField(max_length=20, choices=ContractType.choices)
    other_type_name = models.CharField(max_length=180, blank=True)
    position = models.CharField(max_length=180, blank=True)
    gross_amount = models.DecimalField(
        max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    gross_basis = models.CharField(max_length=20, choices=GrossBasis.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(gross_amount__gte=0), name="contract_gross_nonnegative"
            ),
            models.CheckConstraint(
                condition=models.Q(contract_type__in=ContractType.values),
                name="contract_valid_type",
            ),
            models.CheckConstraint(
                condition=models.Q(gross_basis__in=GrossBasis.values), name="contract_valid_basis"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(contract_type=ContractType.OTHER) & ~models.Q(other_type_name="")
                    | ~models.Q(contract_type=ContractType.OTHER) & models.Q(other_type_name="")
                ),
                name="contract_other_name_matches_type",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(contract_type__in=[ContractType.EMPLOYMENT, ContractType.MANDATE])
                    | models.Q(position="")
                ),
                name="contract_position_matches_type",
            ),
        ]


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(Household, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=20)
    object_type = models.CharField(max_length=50)
    object_id = models.UUIDField()
    occurred_at = models.DateTimeField(auto_now_add=True)
    before = models.JSONField(null=True)
    after = models.JSONField()

    class Meta:
        ordering = ["-occurred_at", "id"]
        indexes = [
            models.Index(fields=["household", "occurred_at"], name="audit_household_time"),
            models.Index(fields=["household", "object_id"], name="audit_household_object"),
        ]


class AccountingMonthState(models.TextChoices):
    INACTIVE = "inactive", "Nieaktywny"
    ACTIVE = "active", "Aktywny"
    CLOSED = "closed", "Zamknięty"


class AccountingYear(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey(
        Household, on_delete=models.PROTECT, related_name="accounting_years"
    )
    calendar_year = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-calendar_year", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["household", "calendar_year"], name="acct_year_household_year_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(calendar_year__gte=1, calendar_year__lte=9999),
                name="acct_year_calendar_year_range",
            ),
        ]


class AccountingMonth(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accounting_year = models.ForeignKey(
        AccountingYear, on_delete=models.PROTECT, related_name="months"
    )
    month_number = models.PositiveSmallIntegerField()
    state = models.CharField(
        max_length=10, choices=AccountingMonthState.choices, default=AccountingMonthState.INACTIVE
    )
    activated_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["month_number", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["accounting_year", "month_number"], name="acct_month_year_number_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(month_number__gte=1, month_number__lte=12),
                name="acct_month_number_range",
            ),
            models.CheckConstraint(
                condition=models.Q(state__in=AccountingMonthState.values),
                name="acct_month_valid_state",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        state=AccountingMonthState.INACTIVE,
                        activated_at__isnull=True,
                        closed_at__isnull=True,
                    )
                    | models.Q(state=AccountingMonthState.ACTIVE, activated_at__isnull=False)
                    | models.Q(
                        state=AccountingMonthState.CLOSED,
                        activated_at__isnull=False,
                        closed_at__isnull=False,
                    )
                ),
                name="acct_month_state_timestamps_valid",
            ),
        ]

    @property
    def month_start(self):
        return date(self.accounting_year.calendar_year, self.month_number, 1)

    @property
    def month_end(self):
        year = self.accounting_year.calendar_year
        last_day = calendar.monthrange(year, self.month_number)[1]
        return date(year, self.month_number, last_day)
