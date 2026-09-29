import { expect, test, type Page } from "@playwright/test";
import type {
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

function archived(id: string, active = true) {
  return {
    id,
    household_id: "home-a",
    is_active: active,
    deactivated_at: active ? null : now,
    created_at: now,
    updated_at: now,
  };
}

function relation(id: string, name: string, active = true): RelationType {
  return { ...archived(id, active), name };
}

function member(id: string, name: string, relationId: string | null = null): HouseholdMember {
  return {
    ...archived(id),
    display_name: name,
    account_id: null,
    relation_type_id: relationId,
  };
}

function income(id: string, memberId: string | null = null): OtherIncomeSource {
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
  requests: { path: string; method: string; body: Record<string, unknown> | null }[];
  denyNextWrite: boolean;
  delayHomeAMembers: Promise<void> | null;
};

function pageOf<T>(items: T[], page: number): Paginated<T> {
  const start = (page - 1) * 50;
  return {
    count: items.length,
    next: start + 50 < items.length ? `https://localhost:8443/api/page=${page + 1}` : null,
    previous: page > 1 ? `https://localhost:8443/api/page=${page - 1}` : null,
    results: items.slice(start, start + 50),
  };
}

async function mockRecords(
  page: Page,
  options: {
    role?: Role;
    relations?: RelationType[];
    members?: HouseholdMember[];
    incomes?: IncomeSource[];
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

    const resource = ["members", "relation-types", "income-sources"].find((name) =>
      suffix.startsWith(`${name}/`),
    );
    if (!resource) return reply({}, 404);
    if (state.denyNextWrite && method !== "GET") {
      state.denyNextWrite = false;
      state.homes[0].role = "viewer";
      return reply({}, 403);
    }
    const records: (HouseholdMember | RelationType | IncomeSource)[] =
      resource === "members"
        ? state.members[home.id]
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
      return reply(record);
    }
    if (method === "POST" && action === "deactivate") {
      Object.assign(record, { is_active: false, deactivated_at: now, updated_at: now });
      return reply(record);
    }
    return reply({}, 405);
  });
  return state;
}

test("Owner dodaje relację, członka i kompletne źródło dochodu bez utraty precyzji", async ({
  page,
}) => {
  const state = await mockRecords(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Członkowie" }).click();
  await expect(page.getByText("Brak członków.", { exact: false })).toBeVisible();
  await page.getByLabel("Nazwa relacji").fill("Rodzic");
  await page.getByRole("button", { name: "Dodaj relację" }).click();
  await expect(page.locator(".record-list strong", { hasText: "Rodzic" })).toBeVisible();

  await page.getByLabel("Nazwa członka").fill("Anna");
  await page.getByLabel("Relacja rodzinna").selectOption({ label: "Rodzic" });
  await page.getByLabel("Powiązane konto").selectOption({ label: "arek" });
  await page.getByRole("button", { name: "Dodaj członka" }).click();
  await expect(page.getByRole("row", { name: /Anna Rodzic arek/ })).toBeVisible();

  await page.getByRole("button", { name: "Dochody" }).click();
  await expect(page.getByText("nie jest rzeczywistą transakcją", { exact: false })).toBeVisible();
  await page.getByLabel("Przypisanie dochodu").selectOption({ label: "Anna" });
  await page.getByLabel("Nazwa źródła").fill("Kontrakt");
  await page.getByLabel("Kategoria").fill("praca");
  await page.getByLabel("Płatnik").fill("Firma");
  await page.getByLabel("Częstotliwość").selectOption("weekly");
  await page.getByLabel("Data rozpoczęcia").fill("2026-01-01");
  await page.getByLabel("Data zakończenia").fill("2026-12-31");
  await page.getByLabel("Domyślna kwota miesięczna").fill("1234567890123456,78");
  await page.getByLabel("Waluta").fill("eur");
  await page.getByLabel("Dochód regularny").uncheck();
  await page.getByLabel("Opis").fill("Kwota planistyczna");
  await page.getByRole("button", { name: "Dodaj źródło" }).click();

  await expect(page.getByRole("row", { name: /Kontrakt/ })).toContainText(
    "1 234 567 890 123 456,78 EUR",
  );
  const write = state.requests.find(
    (item) => item.path.endsWith("/income-sources/") && item.method === "POST",
  );
  expect(write?.body).toMatchObject({
    member_id: "members-1",
    default_monthly_amount: "1234567890123456.78",
    currency: "EUR",
    frequency: "weekly",
    is_regular: false,
    end_date: "2026-12-31",
  });
});

test("edycja i dezaktywacja wymagają świadomego działania oraz zachowują archiwum", async ({
  page,
}) => {
  const source = income("income-1", "member-1");
  await mockRecords(page, {
    relations: [relation("relation-1", "Rodzic")],
    members: [member("member-1", "Anna", "relation-1")],
    incomes: [source],
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Członkowie" }).click();
  const memberRow = page.getByRole("row", { name: /Anna/ });
  await memberRow.getByRole("button", { name: "Edytuj" }).click();
  await page.getByLabel("Nazwa członka").fill("Anna Kowalska");
  await page.getByRole("button", { name: "Zapisz członka" }).click();
  await expect(page.getByRole("row", { name: /Anna Kowalska/ })).toBeVisible();

  page.once("dialog", (dialog) => dialog.dismiss());
  await page
    .getByRole("row", { name: /Anna Kowalska/ })
    .getByRole("button", { name: "Dezaktywuj" })
    .click();
  await expect(page.getByRole("row", { name: /Anna Kowalska/ })).toContainText("Aktywny");
  page.once("dialog", (dialog) => dialog.accept());
  await page
    .getByRole("row", { name: /Anna Kowalska/ })
    .getByRole("button", { name: "Dezaktywuj" })
    .click();
  await expect(page.getByRole("row", { name: /Anna Kowalska/ })).toContainText("Archiwalny");

  await page.getByRole("button", { name: "Dochody" }).click();
  page.once("dialog", (dialog) => dialog.accept());
  await page
    .getByRole("row", { name: /Wynagrodzenie/ })
    .getByRole("button", { name: "Dezaktywuj" })
    .click();
  await expect(page.getByRole("row", { name: /Wynagrodzenie/ })).toContainText("Archiwalne");
});

for (const role of ["member", "viewer"] as const) {
  test(`${role} widzi członków i dochody bez kontrolek zapisu`, async ({ page }) => {
    await mockRecords(page, {
      role,
      relations: [relation("relation-1", "Rodzic")],
      members: [member("member-1", "Anna", "relation-1")],
      incomes: [income("income-1", "member-1")],
    });
    await page.goto("/");
    await page.getByRole("button", { name: "Członkowie" }).click();
    await expect(page.getByText("Tryb odczytu. Członków", { exact: false })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dodaj|Edytuj|Dezaktywuj/ })).toHaveCount(0);
    await page.getByRole("button", { name: "Dochody" }).click();
    await expect(page.getByRole("row", { name: /Wynagrodzenie/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dodaj|Edytuj|Dezaktywuj/ })).toHaveCount(0);
  });
}

test("Administrator zapisuje dane, a odmowa API odświeża rolę do trybu odczytu", async ({
  page,
}) => {
  const state = await mockRecords(page, { role: "administrator" });
  await page.goto("/");
  await page.getByRole("button", { name: "Członkowie" }).click();
  await page.getByLabel("Nazwa członka").fill("Osoba admina");
  await page.getByRole("button", { name: "Dodaj członka" }).click();
  await expect(page.getByText("Osoba admina", { exact: true })).toBeVisible();
  state.denyNextWrite = true;
  await page.getByLabel("Nazwa członka").fill("Odrzucona osoba");
  await page.getByRole("button", { name: "Dodaj członka" }).click();
  await expect(page.getByText("Tryb odczytu. Członków", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Dodaj członka" })).toHaveCount(0);
  expect(state.members["home-a"].some((item) => item.display_name === "Odrzucona osoba")).toBe(
    false,
  );
});

test("paginacja pokazuje dalszych członków i ładuje wszystkie relacje do formularza", async ({
  page,
}) => {
  await mockRecords(page, {
    members: Array.from({ length: 51 }, (_, index) => member(`member-${index}`, `Osoba ${index}`)),
    relations: Array.from({ length: 51 }, (_, index) =>
      relation(`relation-${index}`, `Relacja ${index}`),
    ),
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Członkowie" }).click();
  await expect(page.getByLabel("Relacja rodzinna").locator("option")).toHaveCount(52);
  await expect(page.getByText("Strona 1 z 2")).toBeVisible();
  await page.getByRole("button", { name: "Następna" }).click();
  await expect(page.getByRole("row", { name: /Osoba 50/ })).toBeVisible();
  await expect(page.getByText("Strona 2 z 2")).toBeVisible();
});

test("spóźniona lista członków nie wraca po zmianie gospodarstwa", async ({ page }) => {
  const state = await mockRecords(page, { members: [member("member-a", "Osoba A")] });
  let release!: () => void;
  state.delayHomeAMembers = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Członkowie" }).click();
  await expect(page.getByText("Pobieranie członków i relacji…")).toBeVisible();
  await page.getByLabel("Aktywne gospodarstwo").selectOption("home-b");
  await page.getByRole("button", { name: "Członkowie" }).click();
  await expect(page.getByText("Osoba B", { exact: true })).toBeVisible();
  release();
  await expect(page.getByText("Osoba A", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("Aktywne gospodarstwo")).toHaveValue("home-b");
});

for (const viewport of [
  { width: 1440, height: 900, columns: 3 },
  { width: 1024, height: 768, columns: 2 },
  { width: 390, height: 844, columns: 1 },
]) {
  test(`układ członków i dochodów przy ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await mockRecords(page, {
      relations: [relation("relation-1", "Rodzic")],
      members: [member("member-1", "Anna", "relation-1")],
      incomes: [income("income-1", "member-1")],
    });
    await page.goto("/");
    await expect(page.getByRole("row", { name: /Anna Rodzic/ })).toBeVisible();

    const context = await page.getByLabel("Aktywne gospodarstwo").boundingBox();
    expect(context).not.toBeNull();
    if (viewport.width === 1440) expect(context!.width).toBeLessThanOrEqual(641);
    const panels = page.locator(".member-edit-grid > .panel");
    await expect(panels).toHaveCount(2);
    const memberPanel = await panels.nth(0).boundingBox();
    const relationPanel = await panels.nth(1).boundingBox();
    expect(memberPanel).not.toBeNull();
    expect(relationPanel).not.toBeNull();
    if (viewport.width === 1440) {
      expect(relationPanel!.x).toBeGreaterThan(memberPanel!.x + memberPanel!.width);
      expect(Math.abs(relationPanel!.y - memberPanel!.y)).toBeLessThan(2);
      const role = await page.locator(".context-meta .badge").boundingBox();
      expect(role!.x).toBeGreaterThan(context!.x + context!.width);
    } else {
      expect(relationPanel!.y).toBeGreaterThan(memberPanel!.y + memberPanel!.height);
    }

    const memberForm = await page.locator(".panel-compact-form > form").boundingBox();
    const memberAction = await page.getByRole("button", { name: "Dodaj członka" }).boundingBox();
    expect(memberForm).not.toBeNull();
    expect(memberAction).not.toBeNull();
    if (viewport.width === 390) expect(memberAction!.width).toBeGreaterThan(memberForm!.width - 2);
    else expect(memberAction!.width).toBeLessThan(memberForm!.width / 2);

    if (viewport.width === 390) {
      const table = page.getByRole("region", { name: /Członkowie gospodarstwa/ });
      expect(await table.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(
        true,
      );
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      viewport.width,
    );
    await page.screenshot({
      path: `../memory-bank/bolts/009-household-foundation-ui/evidence/after-members-${viewport.width}.png`,
      fullPage: true,
    });

    await page.getByRole("button", { name: "Dochody" }).click();
    await expect(page.getByRole("row", { name: /Wynagrodzenie/ })).toBeVisible();
    const columns = await page
      .locator(".panel-wide-form .form-grid")
      .evaluate(
        (element) =>
          getComputedStyle(element).gridTemplateColumns.split(" ").filter(Boolean).length,
      );
    expect(columns).toBe(viewport.columns);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      viewport.width,
    );
    await page.screenshot({
      path: `../memory-bank/bolts/009-household-foundation-ui/evidence/after-income-${viewport.width}.png`,
      fullPage: true,
    });
    if (viewport.width <= 1024) {
      const incomeTable = page.getByRole("region", { name: /Źródła dochodu/ });
      expect(
        await incomeTable.evaluate((element) => element.scrollWidth > element.clientWidth),
      ).toBe(true);
      await incomeTable.focus();
      await page.keyboard.press("ArrowRight");
      await expect
        .poll(() => incomeTable.evaluate((element) => element.scrollLeft))
        .toBeGreaterThan(0);
      await incomeTable.evaluate((element) => {
        element.scrollLeft = element.scrollWidth;
      });
      const tableBox = await incomeTable.boundingBox();
      const actionBox = await incomeTable.getByRole("button", { name: "Dezaktywuj" }).boundingBox();
      expect(actionBox!.x + actionBox!.width).toBeLessThanOrEqual(
        tableBox!.x + tableBox!.width + 1,
      );
    }
  });
}

test("ustawienia i tabela dostępów pozostają dostępne klawiaturą", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockRecords(page, { members: [member("member-1", "Anna")] });
  await page.goto("/");
  const incomeLink = page.getByRole("button", { name: "Dochody" });
  await incomeLink.focus();
  await page.keyboard.press("Tab");
  const settingsLink = page.getByRole("button", { name: "Ustawienia" });
  await expect(settingsLink).toBeFocused();
  expect(await settingsLink.evaluate((element) => getComputedStyle(element).outlineWidth)).toBe(
    "3px",
  );
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Dostęp użytkowników" })).toBeVisible();
  for (const control of [
    page.getByLabel("Aktywne gospodarstwo"),
    page.getByLabel("Rola użytkownika arek"),
    page.getByRole("button", { name: "Zapisz rolę" }),
  ]) {
    await control.focus();
    expect(await control.evaluate((element) => element.matches(":focus-visible"))).toBe(true);
  }
  const table = page.getByRole("region", { name: /Dostępy użytkowników/ });
  await table.focus();
  await page.keyboard.press("ArrowRight");
  await expect.poll(() => table.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
});
