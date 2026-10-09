import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { familyFixture, loginFamily } from "./family-live-fixture";
import { type AccountingMonth, type AccountingYear, type Income } from "../app/lib/periods-api";

const runId = process.env.FAMILY_ACCEPTANCE_RUN_ID;
const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYGAAAAAEAAH2FzhVAAAAAElFTkSuQmCC",
  "base64",
);
const pdf = Buffer.from("%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n");
type LiveState = {
  year: AccountingYear;
  month: AccountingMonth;
  income: Income;
  householdSource: string;
};
let state: LiveState;
function yearsPath() {
  return "/api/households/" + familyFixture().data.households[0] + "/accounting-years/";
}
function monthPath() {
  return yearsPath() + state.year.id + "/months/" + state.month.id + "/";
}
async function liveApi<T>(
  page: Page,
  endpoint: string,
  method = "GET",
  data?: unknown,
  status = 200,
): Promise<T> {
  const { url } = familyFixture();
  const headers: Record<string, string> = { Origin: url };
  if (method !== "GET") {
    const setup = await page.request.get(url + "/api/auth/setup/");
    headers["X-CSRFToken"] = (await setup.json()).csrf_token;
  }
  const reply = await page.request.fetch(url + endpoint, { method, headers, data });
  expect(reply.status(), endpoint).toBe(status);
  return reply.status() === 204 ? (undefined as T) : ((await reply.json()) as T);
}
async function navigateMonth(page: Page) {
  await page.getByRole("button", { name: "Okresy i przychody", exact: true }).click();
  const yearCard = page.locator(".period-grid > .panel").filter({
    has: page.getByRole("heading", { name: String(state.year.calendar_year), exact: true }),
  });
  await yearCard.getByRole("button", { name: "Zobacz miesiące" }).click();
  await expect(page.locator(".period-grid > .panel")).toHaveCount(12);
  await page.getByRole("button", { name: "Przychody", exact: true }).nth(3).click();
}
async function changeState(page: Page, action: "Zamknij" | "Otwórz ponownie") {
  await page.getByRole("button", { name: "Rok " + state.year.calendar_year, exact: true }).click();
  const april = page
    .locator(".period-grid > .panel")
    .filter({ has: page.getByRole("heading", { name: "Kwiecień", exact: true }) });
  await april.getByRole("button", { name: action, exact: true }).click();
  await page
    .getByRole("button", {
      name: action === "Zamknij" ? "Zamknij kwiecień" : "Otwórz kwiecień",
      exact: true,
    })
    .click();
  await expect(
    april.getByText(action === "Zamknij" ? "Zamknięty" : "Aktywny", { exact: true }),
  ).toBeVisible();
  await april.getByRole("button", { name: "Przychody", exact: true }).click();
}
function personRow(page: Page) {
  return page.getByRole("row").filter({
    has: page.getByRole("rowheader", { name: new RegExp(state.income.recipient_snapshot.label) }),
  });
}

test.describe.serial("real API acceptance of bolt 016", () => {
  test.skip(!runId, "Requires an isolated FAMILY_ACCEPTANCE_RUN_ID.");
  test("owner: year, independent months, person/household sources, totals, files and conflicts", async ({
    page,
  }, info) => {
    test.setTimeout(120000);
    const fixture = await loginFamily(page, "owner");
    await page.setViewportSize({ width: 1440, height: 900 });
    const existing = await liveApi<{ results: AccountingYear[] }>(page, yearsPath());
    let calendarYear = 2026;
    while (existing.results.some((year) => year.calendar_year === calendarYear)) calendarYear++;
    await page.getByRole("button", { name: "Okresy i przychody", exact: true }).click();
    await page.getByRole("button", { name: "Dodaj rok", exact: true }).click();
    await page.getByLabel("Rok", { exact: true }).fill(String(calendarYear));
    const yearReply = page.waitForResponse(
      (response) =>
        response.url().endsWith("/accounting-years/") && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Utwórz rok", exact: true }).click();
    const yearResponse = await yearReply;
    expect(yearResponse.status()).toBe(201);
    const created = (await yearResponse.json()) as AccountingYear & { months: AccountingMonth[] };
    expect(created.months).toHaveLength(12);
    expect(created.months.every((month) => month.state === "inactive")).toBe(true);
    state = { year: created, month: created.months[3], income: {} as Income, householdSource: "" };
    await expect(page.getByText("Nieaktywny", { exact: true })).toHaveCount(12);
    for (const [index, name] of [
      [9, "październik"],
      [3, "kwiecień"],
    ] as const) {
      await page
        .getByRole("button", { name: "Aktywuj", exact: true })
        .nth(index === 9 ? 9 : 3)
        .click();
      await page.getByRole("button", { name: "Aktywuj " + name, exact: true }).click();
    }
    await expect(page.getByText("Aktywny", { exact: true })).toHaveCount(2);
    await page.getByRole("button", { name: "Przychody", exact: true }).nth(3).click();
    await page.getByRole("button", { name: "Dodaj przychód", exact: true }).click();
    await page.getByLabel("Osoba", { exact: true }).selectOption(fixture.members[0]);
    await page.getByLabel("Źródło dochodu", { exact: true }).selectOption(fixture.salary);
    await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("");
    await page.getByLabel("Faktyczna kwota przychodu").fill("8000,25");
    await page.getByLabel("Data otrzymania").fill("2025-09-30");
    await page.getByLabel("Opcjonalne załączniki (PNG, JPG, PDF)").setInputFiles([
      { name: "dowod.png", mimeType: "image/png", buffer: png },
      { name: "potwierdzenie.pdf", mimeType: "application/pdf", buffer: pdf },
    ]);
    const incomeReply = page.waitForResponse(
      (response) => response.url().endsWith("/incomes/") && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
    const response = await incomeReply;
    expect(response.status()).toBe(201);
    state.income = (await response.json()) as Income;
    expect(state.income.receipt_date).toBe("2025-09-30");
    await expect(page.locator(".notice[role=status]")).toContainText("Dodano załączniki");
    await expect(page.locator(".period-files li")).toHaveCount(2);
    const download = page.waitForEvent("download");
    await page
      .locator(".period-files li")
      .filter({ hasText: "dowod.png" })
      .getByRole("button", { name: "Pobierz" })
      .click();
    const saved = await download;
    const location = info.outputPath("downloaded.png");
    await saved.saveAs(location);
    expect(readFileSync(location)).toEqual(png);

    await page.getByRole("button", { name: "Kwiecień", exact: true }).click();
    await page.getByRole("button", { name: "Dodaj przychód", exact: true }).click();
    await page.getByLabel("Typ odbiorcy").selectOption("household");
    await page.getByLabel("Faktyczna kwota przychodu").fill("100,50");
    await page.getByLabel("Waluta", { exact: true }).fill("EUR");
    await page.getByLabel("Data otrzymania").fill("2025-09-30");
    await page.getByLabel("Źródło dochodu", { exact: true }).focus();
    await page.getByLabel("Źródło dochodu", { exact: true }).selectOption("__create_source__");
    await expect(page.getByLabel("Rodzaj źródła")).toBeFocused();
    await page.getByLabel("Nazwa innego źródła").fill("Lokata UI " + runId + " " + calendarYear);
    await page.getByLabel("Kategoria", { exact: true }).fill("Oszczędności");
    await page.getByLabel("Data rozpoczęcia", { exact: true }).fill("2025-01-01");
    await page.getByText("Dodatkowe informacje", { exact: true }).click();
    await page.getByLabel("Opcjonalna podpowiedź miesięczna").fill("99999,99");
    await page.getByRole("button", { name: "Dodaj inne źródło", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Nowe źródło dochodu" })).toHaveCount(0);
    await expect(page.getByLabel("Źródło dochodu", { exact: true })).not.toHaveValue("");
    state.householdSource = await page.getByLabel("Źródło dochodu", { exact: true }).inputValue();
    await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("100,50");
    expect((await liveApi<{ count: number }>(page, monthPath() + "incomes/")).count).toBe(1);
    await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Zapisane załączniki" })).toBeVisible();
    await page.getByRole("button", { name: "Kwiecień", exact: true }).click();
    await expect(
      page.locator(".period-summary").getByText("8 000,25 PLN", { exact: true }),
    ).toHaveCount(2);
    await expect(
      page.locator(".period-summary").getByText("100,50 EUR", { exact: true }),
    ).toHaveCount(2);
    await changeState(page, "Zamknij");
    await expect(page.getByRole("button", { name: "Dodaj przychód", exact: true })).toHaveCount(0);
    await personRow(page).getByRole("button", { name: "Załączniki" }).click();
    await expect(page.getByRole("button", { name: "Pobierz", exact: true })).toHaveCount(2);
    await expect(page.getByLabel("Wybierz pliki")).toHaveCount(0);
    await changeState(page, "Otwórz ponownie");
    await personRow(page).getByRole("button", { name: "Edytuj", exact: true }).click();
    await page.getByLabel("Faktyczna kwota przychodu").fill("8300,00");
    await liveApi(page, monthPath() + "incomes/" + state.income.id + "/", "PATCH", {
      amount: "9000.00",
      expected_version: state.income.version,
    });
    await page.getByRole("button", { name: "Zapisz zmiany przychodu", exact: true }).click();
    await expect(
      page.getByRole("heading", { name: "Przychód został zmieniony", exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Rozpocznij ręczne scalanie" }).click();
    await expect(
      page.getByRole("heading", { name: "Zachowany szkic do ręcznego porównania" }),
    ).toBeVisible();
    await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("9000.00");
    await page.getByLabel("Faktyczna kwota przychodu").fill("8900,00");
    await page.getByRole("button", { name: "Zapisz zmiany przychodu", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Zapisane załączniki" })).toBeVisible();
    await page
      .locator(".period-files li")
      .filter({ hasText: "potwierdzenie.pdf" })
      .getByRole("button", { name: "Usuń", exact: true })
      .click();
    await page.getByRole("button", { name: "Usuń załącznik", exact: true }).click();
    await expect(page.locator(".period-files li")).toHaveCount(1);
    await page.getByLabel("Wybierz pliki").setInputFiles({
      name: "bad.png",
      mimeType: "image/png",
      buffer: Buffer.from("invalid image"),
    });
    const rejected = page.waitForResponse(
      (reply) => reply.url().endsWith("/attachments/") && reply.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Dodaj pliki", exact: true }).click();
    expect((await rejected).status()).toBe(400);
    await expect(page.locator(".period-files li")).toHaveCount(1);
    await expect(page.locator(".period-files").getByText("bad.png", { exact: true })).toHaveCount(
      0,
    );
    await page
      .getByLabel("Wybierz pliki")
      .setInputFiles({ name: "potwierdzenie.pdf", mimeType: "application/pdf", buffer: pdf });
    await page.getByRole("button", { name: "Dodaj pliki", exact: true }).click();
    await expect(page.locator(".period-files li")).toHaveCount(2);
    await page.getByRole("button", { name: "Kwiecień", exact: true }).click();
    await changeState(page, "Zamknij");
    state.income = await liveApi<Income>(page, monthPath() + "incomes/" + state.income.id + "/");
    writeFileSync(
      path.join(familyFixture().directory, "periods-ui-state.json"),
      JSON.stringify(state),
    );
    await page.screenshot({
      path: info.outputPath("real-summary-1440.jpg"),
      type: "jpeg",
      quality: 75,
      fullPage: true,
    });
  });

  test("administrator: reopening and saving income on mobile", async ({ page }, info) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await loginFamily(page, "administrator");
    await navigateMonth(page);
    await changeState(page, "Otwórz ponownie");
    await page.getByRole("button", { name: "Dodaj przychód", exact: true }).click();
    await page.getByLabel("Typ odbiorcy").selectOption("household");
    await page.getByLabel("Źródło dochodu", { exact: true }).selectOption(state.householdSource);
    await page.getByLabel("Faktyczna kwota przychodu").fill("77,77");
    await page.getByLabel("Waluta", { exact: true }).fill("GBP");
    await page.getByLabel("Data otrzymania").fill("2026-09-30");
    await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Zapisane załączniki" })).toBeVisible();
    await page.getByRole("button", { name: "Kwiecień", exact: true }).click();
    await changeState(page, "Zamknij");
    await expect(
      page.locator(".period-summary").getByText("77,77 GBP", { exact: true }),
    ).toHaveCount(2);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      390,
    );
    await page.screenshot({
      path: info.outputPath("real-summary-390.jpg"),
      type: "jpeg",
      quality: 75,
      fullPage: true,
    });
  });

  for (const role of ["member", "viewer"]) {
    test(
      role + ": read totals and download in closed month; reject foreign data and writes",
      async ({ page }) => {
        const fixture = await loginFamily(page, role);
        await navigateMonth(page);
        await expect(page.getByRole("button", { name: "Dodaj przychód", exact: true })).toHaveCount(
          0,
        );
        await expect(page.getByRole("button", { name: "Edytuj", exact: true })).toHaveCount(0);
        await personRow(page).getByRole("button", { name: "Załączniki" }).click();
        await expect(page.getByRole("button", { name: "Pobierz", exact: true })).toHaveCount(2);
        await expect(page.getByRole("button", { name: "Usuń", exact: true })).toHaveCount(0);
        const download = page.waitForEvent("download");
        await page.getByRole("button", { name: "Pobierz" }).first().click();
        expect((await download).suggestedFilename()).toMatch(/\.(png|pdf)$/);
        await liveApi(
          page,
          "/api/households/" + fixture.households[1] + "/accounting-years/",
          "GET",
          undefined,
          404,
        );
        await liveApi(
          page,
          yearsPath() + state.year.id + "/months/" + state.month.id + "/reopen/",
          "POST",
          {},
          403,
        );
      },
    );
  }

  test("after restart: saved income and private file bytes remain readable", async ({
    page,
  }, info) => {
    state = JSON.parse(
      readFileSync(path.join(familyFixture().directory, "periods-ui-state.json"), "utf8"),
    ) as LiveState;
    await loginFamily(page, "owner");
    await navigateMonth(page);
    const saved = await liveApi<Income>(page, monthPath() + "incomes/" + state.income.id + "/");
    expect(saved.amount).toBe("8900.00");
    await personRow(page).getByRole("button", { name: "Załączniki" }).click();
    await expect(page.locator(".period-files li")).toHaveCount(2);
    const download = page.waitForEvent("download");
    await page
      .locator(".period-files li")
      .filter({ hasText: "dowod.png" })
      .getByRole("button", { name: "Pobierz" })
      .click();
    const file = await download;
    const target = info.outputPath("after-restart.png");
    await file.saveAs(target);
    expect(readFileSync(target)).toEqual(png);
  });
});
