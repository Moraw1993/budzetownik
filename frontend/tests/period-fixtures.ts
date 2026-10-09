import { type Page } from "@playwright/test";
import {
  company,
  contract,
  contractSource,
  income,
  member,
  mockRecords,
  pageOf,
} from "./record-fixtures";
import {
  type AccountingMonth,
  type AccountingYear,
  type Attachment,
  type Income,
} from "../app/lib/periods-api";
import { type Role } from "../app/lib/api";

export async function mockPeriods(page: Page, role: Role = "owner") {
  const firm = company();
  const agreement = contract("contract-1", "member-1", firm);
  const records = await mockRecords(page, {
    role,
    members: [member("member-1", "Anna")],
    companies: [firm],
    contracts: [agreement],
    incomes: [income("source-home"), contractSource(agreement)],
  });
  const year: AccountingYear = {
    id: "year-1",
    household_id: "home-a",
    calendar_year: 2026,
    created_at: "2026-01-01T00:00:00Z",
  };
  const months: AccountingMonth[] = Array.from({ length: 12 }, (_, index) => ({
    id: `month-${index + 1}`,
    accounting_year_id: year.id,
    month_number: index + 1,
    state: "inactive",
    month_start: `2026-${String(index + 1).padStart(2, "0")}-01`,
    month_end: "2026-12-31",
  }));
  const state = {
    records,
    year,
    months,
    years: [year],
    incomes: [] as Income[],
    files: [] as Attachment[],
    calls: [] as {
      path: string;
      method: string;
      body: Record<string, unknown> | null;
      key: string | undefined;
    }[],
    unknownIncome: false,
    unknownFiles: false,
    rejectTransition: false,
    rejectDelete: false,
    rejectPatch: false,
    delayFiles: null as Promise<void> | null,
    sourcesCount: 1,
  };
  await page.route("**/api/households/home-a/accounting-years/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();
    const body = request.headers()["content-type"]?.includes("application/json")
      ? (request.postDataJSON() as Record<string, unknown>)
      : null;
    state.calls.push({ path, method, body, key: request.headers()["idempotency-key"] });
    const reply = (json: unknown, status = 200) => route.fulfill({ json, status });
    if (path.endsWith("accounting-years/")) {
      if (method === "POST") {
        const created = { ...year, id: "year-created", calendar_year: Number(body?.calendar_year) };
        state.years.push(created);
        return reply({ ...created, months }, 201);
      }
      return reply(pageOf(state.years, Number(url.searchParams.get("page") ?? 1)));
    }
    if (path.endsWith("/months/")) return reply(state.months);
    const month =
      state.months.find((item) => path.includes("/" + item.id + "/")) ?? state.months[3];
    const transition = path.match(/\/(activate|close|reopen)\/$/);
    if (transition) {
      if (state.rejectTransition) {
        state.rejectTransition = false;
        month.state = "closed";
        return reply({ detail: "Stan został zmieniony.", code: "accounting_period_conflict" }, 409);
      }
      month.state = transition[1] === "close" ? "closed" : "active";
      return reply(month);
    }
    if (path.endsWith("/income-source-options/"))
      return reply(
        pageOf(
          Array.from({ length: state.sourcesCount }, (_, index) => ({
            id:
              index === 0
                ? url.searchParams.has("member_id")
                  ? "contract-1"
                  : "source-home"
                : "source-" + index,
            name: index === 0 ? "Wynagrodzenie" : "Źródło " + index,
            kind: "other",
            currency: "PLN",
            start_date: "2026-01-01",
            end_date: null,
            contract: null,
          })),
          Number(url.searchParams.get("page") ?? 1),
        ),
      );
    if (path.endsWith("/income-totals/"))
      return reply({
        totals: state.incomes.length
          ? [
              { currency: "PLN", amount: "8000.00" },
              { currency: "EUR", amount: "100.00" },
            ]
          : [],
      });
    if (path.endsWith("/attachments/")) {
      if (method === "GET") {
        const snapshot = [...state.files];
        if (state.delayFiles) await state.delayFiles;
        return reply({ results: snapshot });
      }
      const file = {
        id: "file-1",
        original_name: "dowod.png",
        media_type: "image/png",
        size_bytes: 68,
        created_at: "2026-10-09T00:00:00Z",
      };
      state.files.push(file);
      if (state.unknownFiles) {
        state.unknownFiles = false;
        return route.abort("failed");
      }
      return reply({ results: [file] }, 201);
    }
    if (path.includes("/attachments/")) {
      if (method === "DELETE") {
        state.files = [];
        return route.fulfill({ status: 204 });
      }
      if (path.endsWith("/download/"))
        return route.fulfill({ body: "image", contentType: "image/png" });
      return reply({}, 404);
    }
    if (path.endsWith("/incomes/")) {
      if (method === "GET")
        return reply(pageOf(state.incomes, Number(url.searchParams.get("page") ?? 1)));
      const existing = state.incomes[0];
      const saved: Income = existing ?? {
        ...(body as unknown as Income),
        id: "income-1",
        household_id: "home-a",
        month_id: month.id,
        version: 1,
        recipient_snapshot: {
          label: body?.member_id ? "Anna" : "Dom rodzinny",
          kind: body?.member_id ? "member" : "household",
        },
        source_snapshot: { name: "Wynagrodzenie", kind: "other", contract: null },
      };
      if (!existing) state.incomes.push(saved);
      if (state.unknownIncome) {
        state.unknownIncome = false;
        return route.abort("failed");
      }
      return reply(saved, 201);
    }
    if (path.includes("/incomes/")) {
      const saved = state.incomes[0];
      if (method === "GET") return saved ? reply(saved) : reply({}, 404);
      if (method === "PATCH") {
        if (state.rejectPatch) {
          state.rejectPatch = false;
          saved.amount = "9000.00";
          saved.version++;
          return reply(
            { code: "income_version_conflict", detail: "Przychód został zmieniony." },
            409,
          );
        }
        Object.assign(saved, body, { version: saved.version + 1 });
        return reply(saved);
      }
      if (state.rejectDelete) {
        state.rejectDelete = false;
        saved.version++;
        return reply(
          { code: "income_version_conflict", detail: "Przychód został zmieniony." },
          409,
        );
      }
      state.incomes = [];
      return route.fulfill({ status: 204 });
    }
    return reply({}, 404);
  });
  return state;
}
export async function openMonth(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Okresy i przychody", exact: true }).click();
  await page.getByRole("button", { name: "Zobacz miesiące" }).first().click();
  await page.getByRole("button", { name: "Przychody", exact: true }).nth(3).click();
}
export async function fillIncome(page: Page) {
  await page.getByRole("button", { name: "Dodaj przychód", exact: true }).click();
  await page.getByLabel("Typ odbiorcy").selectOption("household");
  await page.getByLabel("Źródło dochodu", { exact: true }).selectOption("source-home");
  await page.getByLabel("Faktyczna kwota przychodu").fill("8000,00");
  await page.getByLabel("Data otrzymania").fill("2026-03-30");
}
