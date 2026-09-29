import { type Page } from "@playwright/test";
import type {
  Company,
  Contract,
  Household,
  HouseholdMember,
  IncomeSource,
  Membership,
  OtherIncomeSource,
  Paginated,
  RelationType,
  Role,
} from "../app/lib/api";

const now = "2026-09-21T12:00:00Z";

export function archived(id: string, active = true) {
  return {
    id,
    household_id: "home-a",
    is_active: active,
    deactivated_at: active ? null : now,
    created_at: now,
    updated_at: now,
  };
}

export function relation(id: string, name: string, active = true): RelationType {
  return { ...archived(id, active), name };
}

export function member(
  id: string,
  name: string,
  relationId: string | null = null,
): HouseholdMember {
  return {
    ...archived(id),
    display_name: name,
    account_id: null,
    relation_type_id: relationId,
  };
}

export function income(id: string, memberId: string | null = null): OtherIncomeSource {
  return {
    ...archived(id),
    member_id: memberId,
    name: "Wynagrodzenie",
    kind: "other",
    version: 1,
    category: "praca",
    payer: "Pracodawca",
    start_date: "2026-01-01",
    end_date: null,
    default_monthly_amount: "1234.56",
    currency: "PLN",
    frequency: "monthly",
    is_regular: true,
    description: "Pensja podstawowa",
  };
}

type RecordState = {
  homes: Household[];
  relations: Record<string, RelationType[]>;
  members: Record<string, HouseholdMember[]>;
  incomes: Record<string, IncomeSource[]>;
  companies: Record<string, Company[]>;
  contracts: Record<string, Contract[]>;
  rejectWrite: { status: number; body: unknown } | null;
  requests: { path: string; method: string; body: Record<string, unknown> | null }[];
  denyNextWrite: boolean;
  delayHomeAMembers: Promise<void> | null;
};

export function pageOf<T>(items: T[], page: number): Paginated<T> {
  const start = (page - 1) * 50;
  return {
    count: items.length,
    next: start + 50 < items.length ? `/api/page=${page + 1}` : null,
    previous: page > 1 ? `/api/page=${page - 1}` : null,
    results: items.slice(start, start + 50),
  };
}

export async function mockRecords(
  page: Page,
  options: {
    role?: Role;
    relations?: RelationType[];
    members?: HouseholdMember[];
    incomes?: IncomeSource[];
    companies?: Company[];
    contracts?: Contract[];
  } = {},
) {
  const role = options.role ?? "owner";
  const homes: Household[] = [
    {
      id: "home-a",
      name: "Dom rodzinny",
      currency: "PLN",
      role,
      membership_id: "access-a",
    },
    {
      id: "home-b",
      name: "Drugi dom",
      currency: "EUR",
      role,
      membership_id: "access-b",
    },
  ];
  const state: RecordState = {
    homes,
    relations: { "home-a": options.relations ?? [], "home-b": [relation("relation-b", "Inna")] },
    members: { "home-a": options.members ?? [], "home-b": [member("member-b", "Osoba B")] },
    incomes: { "home-a": options.incomes ?? [], "home-b": [income("income-b", "member-b")] },
    companies: { "home-a": options.companies ?? [], "home-b": [] },
    contracts: { "home-a": options.contracts ?? [], "home-b": [] },
    rejectWrite: null,
    requests: [],
    denyNextWrite: false,
    delayHomeAMembers: null,
  };

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();
    const body = (request.postDataJSON() ?? null) as Record<string, unknown> | null;
    state.requests.push({ path, method, body });
    const reply = (data: unknown, status = 200) => route.fulfill({ status, json: data });

    if (method !== "GET" && request.headers()["x-csrftoken"] !== "fixture-csrf")
      return reply({}, 403);
    if (path === "/api/auth/setup/" && method === "GET")
      return reply({ setup_required: false, csrf_token: "fixture-csrf" });
    if (path === "/api/auth/me/") return reply({ id: 1, username: "arek" });
    if (path === "/api/households/") return reply(state.homes);

    const home = state.homes.find((item) => path.startsWith(`/api/households/${item.id}/`));
    if (!home) return reply({}, 404);
    const suffix = path.slice(`/api/households/${home.id}/`.length);
    if (suffix === "memberships/") {
      return reply([
        {
          id: home.membership_id,
          user_id: 1,
          username: home.id === "home-a" ? "arek" : "konto-b",
          role: home.role,
        },
      ] satisfies Membership[]);
    }
    if (suffix === "invitations/") return reply([]);

    const resource = ["members", "relation-types", "income-sources", "companies", "contracts"].find(
      (name) => suffix.startsWith(`${name}/`),
    );
    if (!resource) return reply({}, 404);
    if (state.denyNextWrite && method !== "GET") {
      state.denyNextWrite = false;
      state.homes[0].role = "viewer";
      return reply({}, 403);
    }
    if (state.rejectWrite && method !== "GET") {
      const rejection = state.rejectWrite;
      state.rejectWrite = null;
      return reply(rejection.body, rejection.status);
    }
    const records: (HouseholdMember | RelationType | IncomeSource | Company | Contract)[] =
      resource === "members"
        ? state.members[home.id]
        : resource === "companies"
          ? state.companies[home.id]
          : resource === "contracts"
            ? state.contracts[home.id]
            : resource === "relation-types"
              ? state.relations[home.id]
              : state.incomes[home.id];
    const rest = suffix.slice(`${resource}/`.length);

    if (!rest && method === "GET") {
      if (home.id === "home-a" && resource === "members" && state.delayHomeAMembers)
        await state.delayHomeAMembers;
      return reply(pageOf(records, Number(url.searchParams.get("page") ?? "1")));
    }
    if (!rest && method === "POST") {
      const id = `${resource}-${records.length + 1}`;
      if (resource === "members") {
        state.members[home.id].push({
          ...archived(id),
          display_name: String(body?.display_name ?? ""),
          account_id: body?.account_id === null ? null : Number(body?.account_id),
          relation_type_id: (body?.relation_type_id as string | null) ?? null,
        });
      } else if (resource === "relation-types") {
        state.relations[home.id].push({ ...archived(id), name: String(body?.name ?? "") });
      } else if (resource === "companies") {
        state.companies[home.id].push({
          id,
          household_id: home.id,
          name: String(body?.name),
          is_active: true,
          archived_at: null,
        });
      } else if (resource === "contracts") {
        const company = state.companies[home.id].find((item) => item.id === body?.company_id)!;
        const agreement = {
          ...contract(id, String(body?.member_id), company),
          ...body,
          id,
          kind: "contract",
          version: 1,
          is_active: true,
          deactivated_at: null,
          company,
        } as Contract;
        state.contracts[home.id].push(agreement);
        state.incomes[home.id].push(contractSource(agreement, home.id));
      } else {
        state.incomes[home.id].push({
          ...income(id),
          ...(body as Partial<OtherIncomeSource>),
          kind: "other",
          version: 1,
        });
      }
      return reply(records.at(-1), 201);
    }

    const [id, action] = rest.split("/");
    const record = records.find((item) => item.id === id);
    if (!record) return reply({}, 404);
    if (method === "PATCH") {
      Object.assign(record, body, { updated_at: now });
      if ("version" in record) record.version += 1;
      if (resource === "contracts") {
        const agreement = record as Contract;
        agreement.company = state.companies[home.id].find((item) => item.id === body?.company_id)!;
        Object.assign(
          state.incomes[home.id].find((item) => item.id === id)!,
          contractSource(agreement, home.id),
        );
      }
      return reply(record);
    }
    if (method === "POST" && action === "convert-to-contract") {
      const company = state.companies[home.id].find((item) => item.id === body?.company_id)!;
      const agreement = {
        ...contract(id, String(body?.member_id), company),
        ...body,
        id,
        kind: "contract",
        version: (record as IncomeSource).version + 1,
        is_active: true,
        deactivated_at: null,
        company,
      } as Contract;
      state.contracts[home.id].push(agreement);
      const index = state.incomes[home.id].findIndex((item) => item.id === id);
      state.incomes[home.id][index] = contractSource(agreement, home.id);
      return reply(agreement);
    }
    if (method === "POST" && (action === "deactivate" || action === "archive")) {
      if (resource === "contracts")
        Object.assign(
          state.incomes[home.id].find((item) => item.id === id)!,
          { is_active: false, deactivated_at: now },
        );
      Object.assign(record, { is_active: false, deactivated_at: now, updated_at: now });
      return reply(record);
    }
    return reply({}, 405);
  });
  return state;
}

export function company(id = "company-1", name = "Firma testowa", active = true): Company {
  return { id, name, household_id: "home-a", is_active: active, archived_at: active ? null : now };
}

export function contract(id = "contract-1", memberId = "member-1", firm = company()): Contract {
  return {
    id,
    kind: "contract",
    member_id: memberId,
    name: "Umowa podstawowa",
    start_date: "2026-01-01",
    end_date: null,
    currency: "PLN",
    is_active: true,
    deactivated_at: null,
    version: 1,
    company: firm,
    contract_type: "employment",
    other_type_name: "",
    position: "Programista",
    gross_amount: "7500.25",
    gross_basis: "monthly",
  };
}

export function contractSource(value: Contract, homeId = "home-a"): IncomeSource {
  return {
    ...archived(value.id),
    household_id: homeId,
    member_id: value.member_id,
    name: value.name,
    kind: "contract",
    version: value.version,
    start_date: value.start_date,
    end_date: value.end_date,
    currency: value.currency,
    is_active: value.is_active,
    deactivated_at: value.deactivated_at,
    category: "",
    payer: "",
    default_monthly_amount: null,
    frequency: "",
    is_regular: null,
    description: "",
  };
}
