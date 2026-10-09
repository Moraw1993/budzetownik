import { expect, test } from "@playwright/test";
import { fillIncome, mockPeriods, openMonth } from "./period-fixtures";

test("malformed 201 preserves the attempt and permits safe recovery", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  let first = true;
  let key = "";
  await page.route("**/months/month-4/incomes/", async (route) => {
    if (route.request().method() !== "POST" || !first) return route.fallback();
    first = false;
    key = route.request().headers()["idempotency-key"];
    return route.fulfill({ status: 201, json: {} });
  });
  await openMonth(page);
  await fillIncome(page);
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Nie znamy wyniku zapisu" })).toBeVisible();
  expect(state.calls.some((call) => call.path.includes("undefined"))).toBe(false);
  await page.getByRole("button", { name: "Sprawdź i dokończ poprzedni zapis" }).click();
  await expect(page.getByRole("heading", { name: "Zapisane załączniki" })).toBeVisible();
  expect(state.calls.find((call) => call.method === "POST")?.key).toBe(key);
});
test("definitive rejection resolves unknown state while preserving the draft", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  let first = true;
  await page.route("**/months/month-4/incomes/", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    if (first) {
      first = false;
      return route.abort("failed");
    }
    return route.fulfill({ status: 400, json: { source_id: ["Źródło nie obejmuje okresu."] } });
  });
  await openMonth(page);
  await fillIncome(page);
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await page.getByRole("button", { name: "Sprawdź i dokończ poprzedni zapis" }).click();
  await expect(page.getByRole("heading", { name: "Nie znamy wyniku zapisu" })).toHaveCount(0);
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toBeEnabled();
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("8000,00");
});
test("role loss after failed edit disables remaining writable controls", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  await openMonth(page);
  await fillIncome(page);
  await page.route("**/months/month-4/incomes/", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    state.records.homes[0].role = "viewer";
    return route.fulfill({ status: 403, json: { detail: "Brak uprawnień." } });
  });
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toBeDisabled();
  await expect(page.getByRole("button", { name: "+ Dodaj źródło do słownika" })).toBeDisabled();
});
test("quick source creation protects navigation during a pending write", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  await openMonth(page);
  await fillIncome(page);
  await page.getByRole("button", { name: "+ Dodaj źródło do słownika" }).click();
  await expect(page.getByLabel("Rodzaj źródła")).toBeFocused();
  await page.getByLabel("Nazwa innego źródła").fill("Dodatkowa praca");
  await page.getByLabel("Kategoria", { exact: true }).fill("praca");
  await page.getByLabel("Data rozpoczęcia", { exact: true }).fill("2026-01-01");
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/income-sources/", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    await gate;
    await route.fallback();
  });
  await page.getByRole("button", { name: "Dodaj inne źródło", exact: true }).click();
  await expect(page.getByLabel("Rodzaj źródła")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Anuluj dodawanie źródła" })).toBeDisabled();
  await page.getByRole("button", { name: "Zarządzanie rodziną", exact: true }).click();
  await expect(
    page.getByText("Poczekaj na wynik trwającej operacji.", { exact: true }),
  ).toBeVisible();
  release();
  await expect(page.getByRole("heading", { name: "Dodaj źródło do słownika" })).toHaveCount(0);
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("8000,00");
  expect(state.incomes).toHaveLength(0);
});
test("unknown upload requires a fresh list even when an older GET completes later", async ({
  page,
}) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  state.unknownFiles = true;
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let firstGet = true;
  await page.route("**/attachments/", async (route) => {
    if (route.request().method() !== "GET" || !firstGet) return route.fallback();
    firstGet = false;
    await gate;
    return route.fulfill({ json: { results: [] } });
  });
  await openMonth(page);
  await fillIncome(page);
  await page
    .getByLabel("Opcjonalne załączniki (PNG, JPG, PDF)")
    .setInputFiles({ name: "dowod.png", mimeType: "image/png", buffer: Buffer.from("png") });
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Nie znamy wyniku dodawania plików" }),
  ).toBeVisible();
  release();
  await expect(page.getByText("Brak zapisanych załączników.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ponów po sprawdzeniu listy" })).toBeDisabled();
  await page.getByRole("button", { name: "Sprawdź listę", exact: true }).click();
  await expect(page.getByText("dowod.png", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Ponów po sprawdzeniu listy" })).toBeEnabled();
  await page.getByRole("button", { name: "Zakończ bez ponowienia" }).click();
  expect(
    state.calls.filter((call) => call.method === "POST" && call.path.endsWith("/incomes/")),
  ).toHaveLength(1);
  expect(
    state.calls.filter((call) => call.method === "POST" && call.path.endsWith("/attachments/")),
  ).toHaveLength(1);
});
test("delete conflict displays a message and reselects the current version", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  await openMonth(page);
  await fillIncome(page);
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await page.getByRole("button", { name: "Kwiecień", exact: true }).click();
  state.rejectDelete = true;
  await page.getByRole("button", { name: "Usuń", exact: true }).click();
  await page.getByRole("button", { name: "Usuń przychód", exact: true }).click();
  await expect(page.locator(".notice[role=alert]")).toContainText("Przychód został zmieniony");
  await expect(page.getByRole("heading", { name: "Usuń przychód", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Usuń", exact: true }).click();
  await page.getByRole("button", { name: "Usuń przychód", exact: true }).click();
  await expect(page.getByText("Brak przychodów w tym miesiącu.")).toBeVisible();
  const deletes = state.calls.filter((call) => call.method === "DELETE");
  expect(deletes[1].body?.expected_version).toBe(2);
});
