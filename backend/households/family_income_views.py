from common.serializers import StrictSerializer
from common.views import PrivateAPIView
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .access import require_access
from .family_income_services import write_company, write_contract
from .models import Company, Contract
from .record_serializers import (
    CompanyInput,
    CompanyOutput,
    ContractInput,
    ContractOutput,
    ConversionInput,
)
from .record_views import RecordPagination


def company_queryset(request, household_id):
    require_access(user=request.user, household_id=household_id)
    return Company.objects.filter(household_id=household_id)


def contract_queryset(request, household_id):
    require_access(user=request.user, household_id=household_id)
    return Contract.objects.filter(source__household_id=household_id).select_related(
        "source", "company"
    )


class CompanyListView(PrivateAPIView):
    def get(self, request, household_id):
        query = company_queryset(request, household_id)
        active = request.query_params.get("is_active")
        if active is not None:
            if active not in {"true", "false"}:
                raise ValidationError({"is_active": "Użyj true albo false."})
            query = query.filter(is_active=active == "true")
        paginator = RecordPagination()
        page = paginator.paginate_queryset(query, request)
        return paginator.get_paginated_response(CompanyOutput(page, many=True).data)

    def post(self, request, household_id):
        serializer = CompanyInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = write_company(
            user=request.user, household_id=household_id, data=serializer.validated_data
        )
        return Response(CompanyOutput(company).data, status=201)


class CompanyDetailView(PrivateAPIView):
    def get(self, request, household_id, company_id):
        company = get_object_or_404(company_queryset(request, household_id), pk=company_id)
        return Response(CompanyOutput(company).data)

    def patch(self, request, household_id, company_id):
        serializer = CompanyInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "name" not in serializer.validated_data:
            raise ValidationError({"name": "Podaj nazwę firmy."})
        company = write_company(
            user=request.user,
            household_id=household_id,
            data=serializer.validated_data,
            company_id=company_id,
        )
        return Response(CompanyOutput(company).data)


class CompanyArchiveView(PrivateAPIView):
    def post(self, request, household_id, company_id):
        serializer = StrictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = write_company(
            user=request.user,
            household_id=household_id,
            company_id=company_id,
            data={},
            archive=True,
        )
        return Response(CompanyOutput(company).data)


class ContractListView(PrivateAPIView):
    def get(self, request, household_id):
        query = contract_queryset(request, household_id)
        member_id = request.query_params.get("member_id")
        if member_id is not None:
            field = serializers.UUIDField()
            try:
                member_id = field.run_validation(member_id)
            except serializers.ValidationError as exc:
                raise ValidationError({"member_id": exc.detail}) from exc
            query = query.filter(source__member_id=member_id)
        paginator = RecordPagination()
        page = paginator.paginate_queryset(
            query.order_by("source__created_at", "source_id"), request
        )
        return paginator.get_paginated_response(ContractOutput(page, many=True).data)

    def post(self, request, household_id):
        serializer = ContractInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = write_contract(
            user=request.user, household_id=household_id, data=serializer.validated_data
        )
        return Response(ContractOutput(contract).data, status=201)


class ContractDetailView(PrivateAPIView):
    def get(self, request, household_id, source_id):
        contract = get_object_or_404(contract_queryset(request, household_id), source_id=source_id)
        return Response(ContractOutput(contract).data)

    def patch(self, request, household_id, source_id):
        serializer = ContractInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        contract = write_contract(
            user=request.user,
            household_id=household_id,
            source_id=source_id,
            data=serializer.validated_data,
        )
        return Response(ContractOutput(contract).data)


class ContractArchiveView(PrivateAPIView):
    def post(self, request, household_id, source_id):
        serializer = StrictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = write_contract(
            user=request.user, household_id=household_id, source_id=source_id, data={}, archive=True
        )
        return Response(ContractOutput(contract).data)


class SourceConversionView(PrivateAPIView):
    def post(self, request, household_id, source_id):
        serializer = ConversionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = write_contract(
            user=request.user,
            household_id=household_id,
            source_id=source_id,
            data=serializer.validated_data,
            conversion=True,
        )
        return Response(ContractOutput(contract).data)
