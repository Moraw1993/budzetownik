import uuid

import django.db.models.deletion
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("households", "0005_accountingyear_accountingmonth_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IncomeRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=18)),
                (
                    "currency",
                    models.CharField(
                        max_length=3,
                        validators=[RegexValidator(r"^[A-Z]{3}$")],
                    ),
                ),
                ("receipt_date", models.DateField()),
                ("recipient_snapshot", models.JSONField()),
                ("source_snapshot", models.JSONField()),
                ("version", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "accounting_month",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="income_records",
                        to="households.accountingmonth",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="deleted_income_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "household",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="income_records",
                        to="households.household",
                    ),
                ),
                (
                    "income_source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="income_records",
                        to="households.incomesource",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="income_records",
                        to="households.householdmember",
                    ),
                ),
            ],
            options={
                "ordering": ["receipt_date", "created_at", "id"],
                "indexes": [
                    models.Index(
                        fields=[
                            "household",
                            "accounting_month",
                            "receipt_date",
                            "created_at",
                            "id",
                        ],
                        name="income_record_list_idx",
                    ),
                    models.Index(
                        fields=["household", "accounting_month", "currency"],
                        name="income_record_total_idx",
                    ),
                    models.Index(fields=["household", "member"], name="income_record_member_idx"),
                    models.Index(
                        fields=["household", "income_source"],
                        name="income_record_source_idx",
                    ),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount__gt", 0)),
                        name="income_record_amount_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("version__gte", 1)),
                        name="income_record_version_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("currency__regex", r"^[A-Z]{3}$")),
                        name="income_record_currency_uppercase",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(("deleted_at__isnull", True), ("deleted_by__isnull", True))
                            | models.Q(("deleted_at__isnull", False), ("deleted_by__isnull", False))
                        ),
                        name="income_record_delete_fields_match",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="IncomeCreateIdempotency",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("operation", models.CharField(default="income.create", max_length=32)),
                ("client_key", models.UUIDField()),
                ("fingerprint", models.CharField(max_length=64)),
                ("response_status", models.PositiveSmallIntegerField(default=201)),
                ("response_body", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "household",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="households.household",
                    ),
                ),
                (
                    "income_record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="households.incomerecord",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["household", "actor"], name="income_idem_scope_idx")
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("household", "actor", "operation", "client_key"),
                        name="income_create_idempotency_uniq",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("operation", "income.create")),
                        name="income_idempotency_operation_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("response_status", 201)),
                        name="income_idempotency_status_created",
                    ),
                ],
            },
        ),
    ]
