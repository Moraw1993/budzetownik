import { ApiError } from "./api";
import { type Income, type PeriodContext } from "./periods-api";

// A successful status alone does not identify a saved financial record.
export function confirmedIncome(value: unknown, context: PeriodContext): Income {
  if (!value || typeof value !== "object") throw invalid();
  const record = value as Partial<Income>;
  if (
    typeof record.id !== "string" ||
    !record.id ||
    record.household_id !== context.household.id ||
    record.month_id !== context.month.id ||
    !Number.isInteger(record.version) ||
    Number(record.version) < 1 ||
    !(record.member_id === null || typeof record.member_id === "string") ||
    typeof record.source_id !== "string" ||
    !record.source_id ||
    typeof record.amount !== "string" ||
    !/^[0-9]+\.[0-9]{2}$/.test(record.amount) ||
    typeof record.currency !== "string" ||
    !/^[A-Z]{3}$/.test(record.currency) ||
    typeof record.receipt_date !== "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(record.receipt_date) ||
    typeof record.recipient_snapshot?.label !== "string" ||
    typeof record.source_snapshot?.name !== "string"
  )
    throw invalid();
  return record as Income;
}
function invalid() {
  return new ApiError(0, "Nie można potwierdzić zapisu przychodu. Sprawdź poprzednią próbę.");
}
