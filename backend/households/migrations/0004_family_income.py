import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models
from django.db.models.deletion import PROTECT


class Migration(migrations.Migration):
    dependencies = [
        ("households", "0003_relationtype_householdmember_auditlog_incomesource_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True, default=uuid.uuid4, editable=False, serialize=False
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("deactivated_at", models.DateTimeField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("household", models.ForeignKey("households.Household", on_delete=PROTECT)),
                ("name", models.CharField(max_length=180)),
            ],
            options={
                "ordering": ["created_at", "id"],
                "indexes": [
                    models.Index(
                        fields=["household", "is_active", "name"],
                        name="households__househo_a5d90d_idx",
                    )
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=(
                            models.Q(is_active=True, deactivated_at__isnull=True)
                            | models.Q(is_active=False, deactivated_at__isnull=False)
                        ),
                        name="company_archive_state",
                    )
                ],
            },
        ),
        migrations.RemoveConstraint(model_name="incomesource", name="income_valid_frequency"),
        migrations.AddField(
            model_name="incomesource",
            name="kind",
            field=models.CharField(
                max_length=20,
                choices=[("other", "Inne źródło"), ("contract", "Umowa")],
                default="other",
            ),
        ),
        migrations.AddIndex(
            model_name="incomesource",
            index=models.Index(fields=["household", "kind"], name="income_household_kind_idx"),
        ),
        migrations.AddField(
            model_name="incomesource",
            name="version",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name="incomesource",
            name="category",
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name="incomesource",
            name="default_monthly_amount",
            field=models.DecimalField(
                max_digits=18,
                decimal_places=2,
                validators=[MinValueValidator(Decimal("0"))],
                null=True,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="incomesource",
            name="frequency",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("monthly", "Miesięcznie"),
                    ("weekly", "Tygodniowo"),
                    ("quarterly", "Kwartalnie"),
                    ("yearly", "Rocznie"),
                    ("one_off", "Jednorazowo"),
                    ("irregular", "Nieregularnie"),
                ],
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="incomesource",
            name="is_regular",
            field=models.BooleanField(default=True, null=True, blank=True),
        ),
        migrations.AddConstraint(
            model_name="incomesource",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        kind="other",
                        frequency__in=[
                            "monthly",
                            "weekly",
                            "quarterly",
                            "yearly",
                            "one_off",
                            "irregular",
                        ],
                    )
                    | models.Q(kind="contract", frequency="")
                ),
                name="income_valid_frequency",
            ),
        ),
        migrations.AddConstraint(
            model_name="incomesource",
            constraint=models.CheckConstraint(
                condition=models.Q(kind__in=["other", "contract"]), name="income_valid_kind"
            ),
        ),
        migrations.AddConstraint(
            model_name="incomesource",
            constraint=models.CheckConstraint(
                condition=models.Q(version__gte=1), name="income_valid_version"
            ),
        ),
        migrations.AddConstraint(
            model_name="incomesource",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(kind="other")
                    | models.Q(
                        kind="contract",
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
        ),
        migrations.CreateModel(
            name="Contract",
            fields=[
                (
                    "source",
                    models.OneToOneField(
                        "households.IncomeSource",
                        on_delete=PROTECT,
                        primary_key=True,
                        related_name="contract",
                        serialize=False,
                    ),
                ),
                ("company", models.ForeignKey("households.Company", on_delete=PROTECT)),
                (
                    "contract_type",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("employment", "Umowa o pracę"),
                            ("mandate", "Umowa zlecenie"),
                            ("specific_work", "Umowa o dzieło"),
                            ("other", "Inna umowa"),
                        ],
                    ),
                ),
                ("other_type_name", models.CharField(max_length=180, blank=True)),
                ("position", models.CharField(max_length=180, blank=True)),
                (
                    "gross_amount",
                    models.DecimalField(
                        max_digits=18,
                        decimal_places=2,
                        validators=[MinValueValidator(Decimal("0"))],
                    ),
                ),
                (
                    "gross_basis",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("monthly", "Miesięcznie"),
                            ("hourly", "Godzinowo"),
                            ("total", "Za całość"),
                        ],
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(gross_amount__gte=0),
                        name="contract_gross_nonnegative",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            contract_type__in=["employment", "mandate", "specific_work", "other"]
                        ),
                        name="contract_valid_type",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(gross_basis__in=["monthly", "hourly", "total"]),
                        name="contract_valid_basis",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(contract_type="other") & ~models.Q(other_type_name="")
                            | ~models.Q(contract_type="other") & models.Q(other_type_name="")
                        ),
                        name="contract_other_name_matches_type",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(contract_type__in=["employment", "mandate"])
                            | models.Q(position="")
                        ),
                        name="contract_position_matches_type",
                    ),
                ]
            },
        ),
    ]
