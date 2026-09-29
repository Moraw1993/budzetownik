from common.serializers import StrictSerializer
from common.views import PrivateAPIView
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .access import Capability, require_access
from .models import AuditLog, HouseholdMember, IncomeSource, RelationType
from .record_serializers import (
    AuditFilters,
    AuditOutput,
    IncomeInput,
    IncomeOutput,
    MemberInput,
    MemberOutput,
    RelationInput,
    RelationOutput,
)
from .record_services import write_record


class RecordPagination(PageNumberPagination):
    page_size = 50


class RecordView(PrivateAPIView):
    model = None
    input_serializer = None
    output_serializer = None

    def queryset(self, request, household_id):
        require_access(user=request.user, household_id=household_id)
        return self.model.objects.filter(household_id=household_id)

    def write(self, request, household_id, record_id=None, *, deactivate=False):
        serializer = (StrictSerializer if deactivate else self.input_serializer)(
            data=request.data, partial=record_id is not None
        )
        serializer.is_valid(raise_exception=True)
        record = write_record(
            user=request.user,
            household_id=household_id,
            model=self.model,
            data=serializer.validated_data,
            record_id=record_id,
            deactivate=deactivate,
        )
        return Response(
            self.output_serializer(record).data, status=201 if record_id is None else 200
        )


class RecordListView(RecordView):
    def get(self, request, household_id):
        paginator = RecordPagination()
        page = paginator.paginate_queryset(self.queryset(request, household_id), request)
        return paginator.get_paginated_response(self.output_serializer(page, many=True).data)

    def post(self, request, household_id):
        return self.write(request, household_id)


class RecordDetailView(RecordView):
    def get(self, request, household_id, record_id):
        record = get_object_or_404(self.queryset(request, household_id), pk=record_id)
        return Response(self.output_serializer(record).data)

    def patch(self, request, household_id, record_id):
        return self.write(request, household_id, record_id)


class RecordDeactivateView(RecordView):
    def post(self, request, household_id, record_id):
        return self.write(request, household_id, record_id, deactivate=True)


# Each resource uses the same HTTP lifecycle; business rules stay in the service.
RECORD_RESOURCES = {
    "members": (HouseholdMember, MemberInput, MemberOutput),
    "relation-types": (RelationType, RelationInput, RelationOutput),
    "income-sources": (IncomeSource, IncomeInput, IncomeOutput),
}


class AuditListView(PrivateAPIView):
    def get(self, request, household_id):
        require_access(
            user=request.user, household_id=household_id, capability=Capability.MANAGE_ACCESS
        )
        filters = AuditFilters(
            data={key: value for key, value in request.query_params.items() if key != "page"}
        )
        filters.is_valid(raise_exception=True)
        query = AuditLog.objects.filter(household_id=household_id)
        names = {"since": "occurred_at__gte", "until": "occurred_at__lte"}
        query = query.filter(
            **{names.get(key, key): value for key, value in filters.validated_data.items()}
        )
        paginator = RecordPagination()
        page = paginator.paginate_queryset(query, request)
        return paginator.get_paginated_response(AuditOutput(page, many=True).data)
