from common.views import PrivateAPIView
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .access import require_access
from .income_serializers import (
    IncomeCreateInput,
    IncomeDeleteInput,
    IncomeOutput,
    IncomePatchInput,
    IncomeSourceOptionOutput,
    IncomeSourceOptionsQuery,
    IncomeTotalsOutput,
)
from .income_services import (
    create_income_record,
    delete_income_record,
    income_queryset,
    income_source_options,
    month_income_totals,
    resolve_income_period,
    source_option_data,
    update_income_record,
    year_income_totals,
)


class IdempotencyKeyInput(serializers.Serializer):
    key = serializers.UUIDField()


class IncomePagination(PageNumberPagination):
    page_size = 50


class IncomeListView(PrivateAPIView):
    def get(self, request, household_id, year_id, month_id):
        require_access(user=request.user, household_id=household_id)
        _, month = resolve_income_period(
            household_id=household_id, year_id=year_id, month_id=month_id
        )
        paginator = IncomePagination()
        page = paginator.paginate_queryset(
            income_queryset(household_id=household_id, month_id=month.pk), request
        )
        return paginator.get_paginated_response(IncomeOutput(page, many=True).data)

    def post(self, request, household_id, year_id, month_id):
        serializer = IncomeCreateInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        key_serializer = IdempotencyKeyInput(data={"key": request.headers.get("Idempotency-Key")})
        key_serializer.is_valid(raise_exception=True)
        result = create_income_record(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            data=serializer.validated_data,
            idempotency_key=key_serializer.validated_data["key"],
        )
        return Response(result.body, status=result.status_code)


class IncomeDetailView(PrivateAPIView):
    def get(self, request, household_id, year_id, month_id, income_id):
        require_access(user=request.user, household_id=household_id)
        _, month = resolve_income_period(
            household_id=household_id, year_id=year_id, month_id=month_id
        )
        record = get_object_or_404(
            income_queryset(household_id=household_id, month_id=month.pk), pk=income_id
        )
        return Response(IncomeOutput(record).data)

    def patch(self, request, household_id, year_id, month_id, income_id):
        serializer = IncomePatchInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = update_income_record(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            income_id=income_id,
            data=serializer.validated_data,
        )
        return Response(IncomeOutput(record).data)

    def delete(self, request, household_id, year_id, month_id, income_id):
        serializer = IncomeDeleteInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        delete_income_record(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            income_id=income_id,
            expected_version=serializer.validated_data["expected_version"],
        )
        return Response(status=204)


class IncomeSourceOptionsView(PrivateAPIView):
    def get(self, request, household_id, year_id, month_id):
        query = IncomeSourceOptionsQuery(
            data={key: value for key, value in request.query_params.items() if key != "page"}
        )
        query.is_valid(raise_exception=True)
        sources = income_source_options(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
            member_id=query.validated_data.get("member_id"),
        )
        paginator = IncomePagination()
        page = paginator.paginate_queryset(sources, request)
        serialized_sources = [source_option_data(source) for source in page]
        return paginator.get_paginated_response(
            IncomeSourceOptionOutput(serialized_sources, many=True).data
        )


class MonthIncomeTotalsView(PrivateAPIView):
    def get(self, request, household_id, year_id, month_id):
        totals = month_income_totals(
            user=request.user,
            household_id=household_id,
            year_id=year_id,
            month_id=month_id,
        )
        return Response(IncomeTotalsOutput({"totals": totals}).data)


class YearIncomeTotalsView(PrivateAPIView):
    def get(self, request, household_id, year_id):
        totals = year_income_totals(user=request.user, household_id=household_id, year_id=year_id)
        return Response(IncomeTotalsOutput({"totals": totals}).data)
