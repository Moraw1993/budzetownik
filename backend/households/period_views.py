from common.serializers import StrictSerializer
from common.views import PrivateAPIView
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from .access import require_access
from .models import AccountingMonth, AccountingYear
from .period_serializers import (
    AccountingMonthOutput,
    AccountingYearCreatedOutput,
    AccountingYearInput,
    AccountingYearOutput,
)
from .period_services import create_accounting_year, transition_accounting_month
from .record_views import RecordPagination


class AccountingYearListView(PrivateAPIView):
    def get(self, request, household_id):
        require_access(user=request.user, household_id=household_id)
        paginator = RecordPagination()
        years = AccountingYear.objects.filter(household_id=household_id)
        page = paginator.paginate_queryset(years, request)
        return paginator.get_paginated_response(AccountingYearOutput(page, many=True).data)

    def post(self, request, household_id):
        serializer = AccountingYearInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        year = create_accounting_year(
            user=request.user,
            household_id=household_id,
            calendar_year=serializer.validated_data["calendar_year"],
        )
        year = AccountingYear.objects.prefetch_related(
            Prefetch("months", queryset=AccountingMonth.objects.order_by("month_number"))
        ).get(pk=year.pk)
        return Response(AccountingYearCreatedOutput(year).data, status=201)


class AccountingMonthListView(PrivateAPIView):
    def get(self, request, household_id, year_id):
        require_access(user=request.user, household_id=household_id)
        year = get_object_or_404(
            AccountingYear.objects.filter(household_id=household_id), pk=year_id
        )
        months = AccountingMonth.objects.filter(accounting_year=year).select_related(
            "accounting_year"
        )
        return Response(AccountingMonthOutput(months, many=True).data)


class AccountingMonthTransitionView(PrivateAPIView):
    operation = None

    def post(self, request, household_id, year_id, month_id):
        serializer = StrictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        month = transition_accounting_month(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            operation=self.operation,
        )
        return Response(AccountingMonthOutput(month).data)
