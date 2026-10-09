import { expect, test } from "@playwright/test";
import { fillIncome, mockPeriods, openMonth } from "./period-fixtures";

test("12 months remain inactive until an explicit confirmed action", async ({ page }) => {
  const state = await mockPeriods(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Okresy i przychody", exact: true }).click();
  await page.getByRole("button", { name: "Zobacz miesiące" }).click();
  await expect(page.locator(".period-state")).toHaveCount(12);
  await expect(page.getByText("Nieaktywny", { exact: true })).toHaveCount(12);
  await page.getByRole("button", { name: "Aktywuj", exact: true }).nth(9).click();
  expect(state.calls.filter((call) => call.method === "POST")).toHaveLength(0);
  await page.getByRole("button", { name: "Aktywuj październik", exact: true }).click();
  await expect(page.getByText("Aktywny", { exact: true })).toHaveCount(1);
  await page.getByRole("button", { name: "Aktywuj", exact: true }).first().click();
  await page.getByRole("button", { name: "Aktywuj styczeń", exact: true }).click();
  await expect(page.getByText("Aktywny", { exact: true })).toHaveCount(2);
  expect(state.months[9].state).toBe("active");
});
test("unknown income retries the same key and payload then displays real saved data", async ({
  page,
}) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  state.unknownIncome = true;
  await openMonth(page);
  await fillIncome(page);
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Nie znamy wyniku zapisu" })).toBeVisible();
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toBeDisabled();
  await page.getByRole("button", { name: "Sprawdź i dokończ poprzedni zapis" }).click();
  await expect(page.getByRole("heading", { name: "Zapisane załączniki" })).toBeVisible();
  const attempts = state.calls.filter(
    (call) => call.method === "POST" && call.path.endsWith("/incomes/"),
  );
  expect(attempts).toHaveLength(2);
  expect(attempts[0].key).toBe(attempts[1].key);
  expect(attempts[0].body).toEqual(attempts[1].body);
  expect(attempts[0].body?.receipt_date).toBe("2026-03-30");
  expect(state.incomes).toHaveLength(1);
});
test("conflict retains scratch and uses current version only after manual merge", async ({
  page,
}) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  await openMonth(page);
  await fillIncome(page);
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await page.getByRole("button", { name: "Kwiecień", exact: true }).click();
  await page.getByRole("button", { name: "Edytuj", exact: true }).click();
  await page.getByLabel("Faktyczna kwota przychodu").fill("8500,00");
  state.rejectPatch = true;
  await page.getByRole("button", { name: "Zapisz zmiany przychodu" }).click();
  await expect(page.getByRole("heading", { name: "Przychód został zmieniony" })).toBeVisible();
  await page.getByRole("button", { name: "Rozpocznij ręczne scalanie" }).click();
  await expect(
    page.getByRole("heading", { name: "Zachowany szkic do ręcznego porównania" }),
  ).toBeVisible();
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("9000.00");
  await page.getByLabel("Faktyczna kwota przychodu").fill("8600,00");
  await page.getByRole("button", { name: "Zapisz zmiany przychodu" }).click();
  await expect(page.getByRole("heading", { name: "Zapisane załączniki" })).toBeVisible();
  const patches = state.calls.filter((call) => call.method === "PATCH");
  expect(patches[1].body).toEqual({ amount: "8600.00", expected_version: 2 });
});
test("state conflicts remain visible and require selecting fresh data", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  state.rejectTransition = true;
  await page.goto("/");
  await page.getByRole("button", { name: "Okresy i przychody" }).click();
  await page.getByRole("button", { name: "Zobacz miesiące" }).click();
  await page.getByRole("button", { name: "Zamknij", exact: true }).click();
  await page.getByRole("button", { name: "Zamknij kwiecień" }).click();
  await expect(page.locator(".notice[role=alert]")).toContainText("Stan został zmieniony");
  await expect(page.getByText("Zamknięty", { exact: true })).toBeVisible();
});
test("viewer reads inactive month without writable controls", async ({ page }) => {
  const state = await mockPeriods(page, "viewer");
  await openMonth(page);
  await expect(
    page.getByRole("heading", { name: "Przychody miesiąca", exact: true }).last(),
  ).toBeAttached();
  await expect(page.getByRole("button", { name: "Dodaj przychód", exact: true })).toHaveCount(0);
  await expect(page.getByText("Brak przychodów", { exact: true })).toHaveCount(2);
  expect(state.calls.filter((call) => call.method !== "GET")).toHaveLength(0);
});
test("dirty navigation asks before discarding and cancellation keeps input", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  await openMonth(page);
  await fillIncome(page);
  await page.getByRole("button", { name: "Zarządzanie rodziną", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Masz niezapisane zmiany" })).toBeVisible();
  await page.getByRole("button", { name: "Anuluj", exact: true }).first().click();
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("8000,00");
});
test("all source pages load without auto-filling actual income", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  state.sourcesCount = 51;
  await openMonth(page);
  await page.getByRole("button", { name: "Dodaj przychód", exact: true }).click();
  await page.getByLabel("Typ odbiorcy").selectOption("household");
  await page.getByLabel("Źródło dochodu", { exact: true }).selectOption("source-50");
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("");
});
for (const width of [1440, 1024, 390]) {
  test(`form geometry and overflow at ${width}px`, async ({ page }, testInfo) => {
    const state = await mockPeriods(page);
    state.months[3].state = "active";
    await page.setViewportSize({ width, height: 900 });
    await openMonth(page);
    await fillIncome(page);
    await page.evaluate(() => document.fonts.ready);
    const measurements = await page.evaluate(() => ({
      page: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
      heights: Array.from(
        document.querySelectorAll(".period-form-grid input,.period-form-grid select"),
      ).map((node) => node.getBoundingClientRect().height),
    }));
    expect(measurements.scroll).toBeLessThanOrEqual(measurements.page);
    expect(measurements.heights.every((height) => height === 46)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`income-${width}.png`), fullPage: true });
  });
}
