import { expect, test } from "@playwright/test";
import { fillIncome, mockPeriods, openMonth } from "./period-fixtures";

for (const width of [1440, 1024, 390]) {
  test(`approved contextual views at ${width}px`, async ({ page }, testInfo) => {
    const state = await mockPeriods(page);
    state.months[3].state = "active";
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await page.getByRole("button", { name: "Okresy i przychody", exact: true }).click();
    const capture = async (name: string) => {
      await page.evaluate(() => document.fonts.ready);
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
        width,
      );
      await page.screenshot({
        path: testInfo.outputPath(`${name}-${width}.jpg`),
        type: "jpeg",
        quality: 75,
        fullPage: true,
      });
    };
    await expect(
      page.getByRole("heading", { name: "Lata rozliczeniowe", exact: true }).last(),
    ).toBeVisible();
    await capture("years");
    await page.getByRole("button", { name: "Zobacz miesiące" }).click();
    await expect(page.locator(".period-state")).toHaveCount(12);
    await capture("months");
    await page.getByRole("button", { name: "Przychody", exact: true }).nth(3).click();
    await expect(page.getByText("Brak przychodów w tym miesiącu.")).toBeVisible();
    await capture("summary-empty");
    await fillIncome(page);
    await capture("income");
    await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Zapisane załączniki" })).toBeVisible();
    await capture("attachments");
    await page.getByRole("button", { name: "Kwiecień", exact: true }).click();
    await expect(page.getByRole("cell", { name: "8 000,00 PLN", exact: true })).toBeVisible();
    await capture("summary");
    await expect(page.getByRole("button", { name: "Formularz", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Podsumowanie", exact: true })).toHaveCount(0);
  });
}
test("private file upload, download and confirmed removal do not recreate income", async ({
  page,
}) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  await openMonth(page);
  await fillIncome(page);
  await page
    .getByLabel("Opcjonalne załączniki (PNG, JPG, PDF)")
    .setInputFiles({ name: "dowod.png", mimeType: "image/png", buffer: Buffer.from("png") });
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await expect(page.locator(".notice[role=status]")).toContainText("Dodano załączniki");
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Pobierz", exact: true }).click();
  expect((await downloaded).suggestedFilename()).toBe("dowod.png");
  await page.getByRole("button", { name: "Usuń", exact: true }).click();
  await page.getByRole("button", { name: "Usuń załącznik", exact: true }).click();
  await expect(page.getByText("Brak zapisanych załączników.")).toBeVisible();
  expect(
    state.calls.filter((call) => call.method === "POST" && call.path.endsWith("/incomes/")),
  ).toHaveLength(1);
});
test("membership loss removes inaccessible views even when months return 403", async ({ page }) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  await openMonth(page);
  await fillIncome(page);
  await page.route("**/months/month-4/incomes/", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    state.records.homes = [];
    return route.fulfill({ status: 403, json: { detail: "Brak członkostwa." } });
  });
  await page.route("**/accounting-years/year-1/months/", async (route) => {
    if (state.records.homes.length) return route.fallback();
    return route.fulfill({ status: 403, json: {} });
  });
  await page.getByRole("button", { name: "Zapisz przychód", exact: true }).click();
  await expect(
    page.getByText("Dane lub dostęp do gospodarstwa są niedostępne. Odśwież aplikację."),
  ).toBeVisible();
  await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveCount(0);
});
