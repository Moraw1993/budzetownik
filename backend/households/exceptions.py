from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class LastOwnerError(APIException):
    status_code = 409
    default_detail = "Gospodarstwo musi zachować co najmniej jednego Owner."
    default_code = "last_owner"


class SourceConflict(APIException):
    status_code = 409
    default_detail = "Źródło zmieniło się albo ma już inny rodzaj."
    default_code = "source_conflict"


class AccountingPeriodConflict(APIException):
    status_code = 409
    default_detail = "Rok lub miesiąc rozliczeniowy jest już w innym stanie."
    default_code = "accounting_period_conflict"


class IncomePeriodConflict(APIException):
    status_code = 409
    default_detail = "Miesiąc rozliczeniowy musi być aktywny, aby zmienić przychód."
    default_code = "income_period_not_active"


class IncomeVersionConflict(APIException):
    status_code = 409
    default_detail = "Przychód został zmieniony. Odśwież dane i spróbuj ponownie."
    default_code = "income_version_conflict"


class IdempotencyConflict(APIException):
    status_code = 409
    default_detail = "Klucz idempotencji został użyty dla innego żądania."
    default_code = "idempotency_conflict"


def household_exception_handler(exc, context):
    response = exception_handler(exc, context)
    conflict_types = (
        AccountingPeriodConflict
        | LastOwnerError
        | SourceConflict
        | IncomePeriodConflict
        | IncomeVersionConflict
        | IdempotencyConflict
    )
    if response is not None and isinstance(exc, conflict_types):
        response.data["code"] = exc.get_codes()
    return response
