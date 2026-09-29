from django.urls import path

from .family_income_views import (
    CompanyArchiveView,
    CompanyDetailView,
    CompanyListView,
    ContractArchiveView,
    ContractDetailView,
    ContractListView,
    SourceConversionView,
)
from .record_views import (
    RECORD_RESOURCES,
    AuditListView,
    RecordDeactivateView,
    RecordDetailView,
    RecordListView,
)
from .views import (
    HouseholdDetailView,
    HouseholdListView,
    InvitationDetailView,
    InvitationListView,
    MembershipDetailView,
    MembershipListView,
    OwnershipTransferView,
)

urlpatterns = [
    path("<uuid:household_id>/audit-logs/", AuditListView.as_view(), name="audit-list"),
    path("<uuid:household_id>/companies/", CompanyListView.as_view(), name="company-list"),
    path(
        "<uuid:household_id>/companies/<uuid:company_id>/",
        CompanyDetailView.as_view(),
        name="company-detail",
    ),
    path(
        "<uuid:household_id>/companies/<uuid:company_id>/archive/",
        CompanyArchiveView.as_view(),
        name="company-archive",
    ),
    path("<uuid:household_id>/contracts/", ContractListView.as_view(), name="contract-list"),
    path(
        "<uuid:household_id>/contracts/<uuid:source_id>/",
        ContractDetailView.as_view(),
        name="contract-detail",
    ),
    path(
        "<uuid:household_id>/contracts/<uuid:source_id>/archive/",
        ContractArchiveView.as_view(),
        name="contract-archive",
    ),
    path(
        "<uuid:household_id>/income-sources/<uuid:source_id>/convert-to-contract/",
        SourceConversionView.as_view(),
        name="income-source-convert-to-contract",
    ),
    path("", HouseholdListView.as_view(), name="household-list"),
    path("<uuid:household_id>/", HouseholdDetailView.as_view(), name="household-detail"),
    path(
        "<uuid:household_id>/memberships/",
        MembershipListView.as_view(),
        name="membership-list",
    ),
    path(
        "<uuid:household_id>/memberships/<uuid:membership_id>/",
        MembershipDetailView.as_view(),
        name="membership-detail",
    ),
    path(
        "<uuid:household_id>/transfer-ownership/",
        OwnershipTransferView.as_view(),
        name="ownership-transfer",
    ),
    path(
        "<uuid:household_id>/invitations/",
        InvitationListView.as_view(),
        name="invitation-list",
    ),
    path(
        "<uuid:household_id>/invitations/<uuid:invitation_id>/",
        InvitationDetailView.as_view(),
        name="invitation-detail",
    ),
]

for resource, (model, input_serializer, output_serializer) in RECORD_RESOURCES.items():
    options = {
        "model": model,
        "input_serializer": input_serializer,
        "output_serializer": output_serializer,
    }
    urlpatterns += [
        path(
            f"<uuid:household_id>/{resource}/",
            RecordListView.as_view(**options),
            name=f"{resource}-list",
        ),
        path(
            f"<uuid:household_id>/{resource}/<uuid:record_id>/",
            RecordDetailView.as_view(**options),
            name=f"{resource}-detail",
        ),
        path(
            f"<uuid:household_id>/{resource}/<uuid:record_id>/deactivate/",
            RecordDeactivateView.as_view(**options),
            name=f"{resource}-deactivate",
        ),
    ]
