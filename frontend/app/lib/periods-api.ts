import {
  api,
  apiBlob,
  apiAllPages,
  ApiError,
  householdPath,
  type Household,
  type Paginated,
} from "./api";

export type AccountingYear = {
  id: string;
  household_id: string;
  calendar_year: number;
  created_at: string;
};
export type MonthState = "inactive" | "active" | "closed";
export type AccountingMonth = {
  id: string;
  accounting_year_id: string;
  month_number: number;
  state: MonthState;
  month_start: string;
  month_end: string;
};
export type IncomeValues = {
  member_id: string | null;
  source_id: string;
  amount: string;
  currency: string;
  receipt_date: string;
};
export type Income = IncomeValues & {
  id: string;
  household_id: string;
  month_id: string;
  version: number;
  recipient_snapshot: { label: string; kind: "member" | "household" };
  source_snapshot: { name: string; kind: string; contract: { company_name: string } | null };
};
export type SourceOption = {
  id: string;
  name: string;
  kind: string;
  currency: string;
  start_date: string;
  end_date: string | null;
  contract: {
    company_name: string;
    company_id: string;
    other_type_name: string | null;
    contract_type: string;
  } | null;
};
export type CurrencyTotal = { currency: string; amount: string };
export type Attachment = {
  id: string;
  original_name: string;
  media_type: string;
  size_bytes: number;
  created_at: string;
};
export type PeriodContext = { household: Household; year: AccountingYear; month: AccountingMonth };
export const monthNames = [
  "Styczeń",
  "Luty",
  "Marzec",
  "Kwiecień",
  "Maj",
  "Czerwiec",
  "Lipiec",
  "Sierpień",
  "Wrzesień",
  "Październik",
  "Listopad",
  "Grudzień",
];
export const stateLabels: Record<MonthState, string> = {
  inactive: "Nieaktywny",
  active: "Aktywny",
  closed: "Zamknięty",
};
export function canManage(household: Household) {
  return household.role === "owner" || household.role === "administrator";
}
export function periodPath(context: PeriodContext, resource = "") {
  return householdPath(
    context.household.id,
    `accounting-years/${encodeURIComponent(context.year.id)}/months/${encodeURIComponent(context.month.id)}/${resource}`,
  );
}
export function incomePath(context: PeriodContext, id: string, resource = "") {
  return periodPath(context, `incomes/${encodeURIComponent(id)}/${resource}`);
}
export function years(household: Household, page: number, signal?: AbortSignal) {
  return api<Paginated<AccountingYear>>(
    householdPath(household.id, `accounting-years/?page=${page}`),
    { signal },
  );
}
export function months(household: Household, year: AccountingYear, signal?: AbortSignal) {
  return api<AccountingMonth[]>(
    householdPath(household.id, `accounting-years/${year.id}/months/`),
    { signal },
  );
}
export function sourceOptions(
  context: PeriodContext,
  memberId: string | null,
  signal?: AbortSignal,
) {
  return apiAllPages<SourceOption>(
    periodPath(
      context,
      `income-source-options/${memberId ? "?member_id=" + encodeURIComponent(memberId) : ""}`,
    ),
    signal,
  );
}
export function uncertain(error: unknown) {
  return error instanceof ApiError && (error.status === 0 || error.status >= 500);
}
export function validateFiles(files: File[], saved: Attachment[] = []): string {
  if (!files.length || files.length > 5) return "Wybierz od 1 do 5 plików.";
  if (files.some((file) => !/\.(png|jpe?g|pdf)$/i.test(file.name)))
    return "Dozwolone pliki: PNG, JPG, JPEG i PDF.";
  if (files.some((file) => file.size === 0 || file.size > 10 * 1024 ** 2))
    return "Każdy plik musi mieć od 1 bajta do 10 MiB.";
  const bytes = files.reduce((sum, file) => sum + file.size, 0);
  if (bytes > 25 * 1024 ** 2) return "Jedna partia może mieć najwyżej 25 MiB.";
  if (
    saved.length + files.length > 20 ||
    saved.reduce((sum, file) => sum + file.size_bytes, 0) + bytes > 50 * 1024 ** 2
  )
    return "Limit przychodu: 20 plików i 50 MiB.";
  return "";
}
export async function attachmentList(
  context: PeriodContext,
  incomeId: string,
  signal?: AbortSignal,
) {
  return (
    await api<{ results: Attachment[] }>(incomePath(context, incomeId, "attachments/"), { signal })
  ).results;
}
export async function uploadFiles(
  context: PeriodContext,
  incomeId: string,
  files: File[],
  signal?: AbortSignal,
) {
  const saved = await attachmentList(context, incomeId, signal);
  const error = validateFiles(files, saved);
  if (error) throw new ApiError(400, error);
  const data = new FormData();
  files.forEach((file) => data.append("files", file));
  const reply = await api<{ results: Attachment[] }>(
    incomePath(context, incomeId, "attachments/"),
    { method: "POST", data, signal, expectedStatus: 201 },
  );
  if (
    !Array.isArray(reply.results) ||
    reply.results.length !== files.length ||
    reply.results.some(
      (item) =>
        typeof item.id !== "string" ||
        typeof item.original_name !== "string" ||
        typeof item.media_type !== "string" ||
        typeof item.size_bytes !== "number" ||
        typeof item.created_at !== "string",
    )
  )
    throw new ApiError(0, "Nie można potwierdzić dodania plików. Sprawdź listę.");
  return reply.results;
}
export async function downloadFile(
  context: PeriodContext,
  incomeId: string,
  file: Attachment,
  signal?: AbortSignal,
) {
  const blob = await apiBlob(
    incomePath(context, incomeId, `attachments/${file.id}/download/`),
    signal,
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = file.original_name;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
