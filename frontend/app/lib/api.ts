export type Role = "owner" | "administrator" | "member" | "viewer";
export type User = { id: number; username: string };
export type Household = {
  id: string;
  name: string;
  currency: string;
  role: Role;
  membership_id: string;
};
export type Membership = { id: string; user_id: number; username: string; role: Role };
export type Invitation = {
  id: string;
  role: Role;
  expires_at: string;
  revoked_at: string | null;
  accepted_at: string | null;
  invitation_url?: string;
};
export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
export type ArchivedRecord = {
  id: string;
  household_id: string;
  is_active: boolean;
  deactivated_at: string | null;
  created_at: string;
  updated_at: string;
};
export type RelationType = ArchivedRecord & { name: string };
export type HouseholdMember = ArchivedRecord & {
  display_name: string;
  account_id: number | null;
  relation_type_id: string | null;
};
export type IncomeFrequency =
  "monthly" | "weekly" | "quarterly" | "yearly" | "one_off" | "irregular";
type IncomeSourceBase = ArchivedRecord & {
  name: string;
  version: number;
  start_date: string;
  end_date: string | null;
  currency: string;
};
export type OtherIncomeSource = IncomeSourceBase & {
  kind: "other";
  member_id: string | null;
  category: string;
  payer: string;
  default_monthly_amount: string | null;
  frequency: IncomeFrequency;
  is_regular: boolean;
  description: string;
};
export type ContractIncomeSource = IncomeSourceBase & {
  kind: "contract";
  member_id: string;
  category: "";
  payer: "";
  default_monthly_amount: null;
  frequency: "";
  is_regular: null;
  description: "";
};
export type IncomeSource = OtherIncomeSource | ContractIncomeSource;
export type Company = {
  id: string;
  household_id: string;
  name: string;
  is_active: boolean;
  archived_at: string | null;
};
export type ContractType = "employment" | "mandate" | "specific_work" | "other";
export type GrossBasis = "monthly" | "hourly" | "total";
export type Contract = {
  id: string;
  kind: "contract";
  member_id: string;
  name: string;
  start_date: string;
  end_date: string | null;
  currency: string;
  is_active: boolean;
  deactivated_at: string | null;
  version: number;
  company: Pick<Company, "id" | "name" | "is_active">;
  contract_type: ContractType;
  other_type_name: string;
  position: string;
  gross_amount: string;
  gross_basis: GrossBasis;
};
export const roleLabels: Record<Role, string> = {
  owner: "Owner",
  administrator: "Administrator",
  member: "Member",
  viewer: "Viewer",
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public fields: Record<string, string> = {},
    public code: string | null = null,
  ) {
    super(message);
  }
}

function errorFromResponse(status: number, body: unknown): ApiError {
  if (
    status === 409 &&
    body &&
    typeof body === "object" &&
    "detail" in body &&
    body.detail === "Konfiguracja początkowa została zakończona."
  ) {
    return new ApiError(409, "Pierwsze konto już istnieje. Odśwież stronę i zaloguj się.");
  }
  if (status >= 500)
    return new ApiError(status, "Serwer jest chwilowo niedostępny. Spróbuj ponownie.");
  const messages: Record<number, string> = {
    401: "Nieprawidłowy login lub hasło.",
    403: "Brak uprawnień lub sesja wygasła. Odśwież dostęp i spróbuj ponownie.",
    404: "Dane są niedostępne. Odśwież listę gospodarstw.",
    409: "Dane zmieniły się od ostatniego odczytu. Odśwież widok i spróbuj ponownie.",
    429: "Zbyt wiele prób. Spróbuj ponownie za 15 minut.",
  };
  const fields: Record<string, string> = {};
  if (status === 400 && body && typeof body === "object") {
    for (const [key, value] of Object.entries(body)) {
      if (
        [
          "username",
          "password",
          "name",
          "currency",
          "role",
          "display_name",
          "account_id",
          "relation_type_id",
          "member_id",
          "category",
          "payer",
          "start_date",
          "end_date",
          "default_monthly_amount",
          "frequency",
          "is_regular",
          "description",
          "company_id",
          "contract_type",
          "other_type_name",
          "position",
          "gross_amount",
          "gross_basis",
          "expected_version",
        ].includes(key)
      ) {
        const text = Array.isArray(value) ? value.join(" ") : value;
        if (typeof text === "string") fields[key] = text.slice(0, 500);
      }
    }
  }
  const detail =
    body && typeof body === "object" && "detail" in body && typeof body.detail === "string"
      ? body.detail
      : null;
  const code =
    body && typeof body === "object" && "code" in body && typeof body.code === "string"
      ? body.code
      : null;
  const conflictMessages: Record<string, string> = {
    last_owner: "Gospodarstwo musi zachować co najmniej jednego aktywnego Ownera.",
    source_conflict: "Źródło zmieniło się od ostatniego odczytu. Odśwież dane i spróbuj ponownie.",
  };
  return new ApiError(
    status,
    (status === 409 && code ? conflictMessages[code] : null) ??
      detail?.slice(0, 500) ??
      messages[status] ??
      "Nie udało się zapisać. Sprawdź pola formularza i spróbuj ponownie.",
    fields,
    code,
  );
}

export async function api<T>(
  path: string,
  options: { method?: string; data?: unknown; signal?: AbortSignal } = {},
): Promise<T> {
  const method = options.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (method !== "GET") {
    // Fetch a fresh token for every write, including after Django rotates the session.
    const setup = await api<{ csrf_token: string }>("/auth/setup/", { signal: options.signal });
    headers["X-CSRFToken"] = setup.csrf_token;
    headers["Content-Type"] = "application/json";
  }
  let response: Response;
  try {
    response = await fetch("/api" + path, {
      method,
      headers,
      credentials: "same-origin",
      cache: "no-store",
      body: options.data === undefined ? undefined : JSON.stringify(options.data),
      signal: options.signal
        ? AbortSignal.any([options.signal, AbortSignal.timeout(15000)])
        : AbortSignal.timeout(15000),
    });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new ApiError(
      0,
      "Nie można połączyć się z aplikacją. Sprawdź, czy jest uruchomiona, i ponów próbę.",
    );
  }
  const body: unknown =
    response.status === 204 ? undefined : await response.json().catch(() => null);
  if (!response.ok) throw errorFromResponse(response.status, body);
  if (body === null) throw new ApiError(0, "Otrzymano nieprawidłową odpowiedź. Spróbuj ponownie.");
  return body as T;
}

export function messageOf(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Nie udało się wykonać operacji. Spróbuj ponownie.";
}

export function householdPath(id: string, resource = ""): string {
  return "/households/" + encodeURIComponent(id) + "/" + resource;
}

export async function apiAllPages<T>(path: string, signal?: AbortSignal): Promise<T[]> {
  const first = await api<Paginated<T>>(path, { signal });
  const results = [...first.results];
  const pages = Math.ceil(first.count / 50);
  for (let page = 2; page <= pages; page += 1) {
    const separator = path.includes("?") ? "&" : "?";
    const next = await api<Paginated<T>>(`${path}${separator}page=${page}`, { signal });
    results.push(...next.results);
  }
  return results;
}
