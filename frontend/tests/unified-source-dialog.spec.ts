import { expect, test, type Page } from "@playwright/test";
import { fillIncome, mockPeriods, openMonth } from "./period-fixtures";

const dialogOf = (page: Page) => page.getByRole("dialog", { name: "Nowe źródło dochodu" });

async function shape(page: Page) {
  return dialogOf(page).evaluate((dialog) => {
    const box = dialog.getBoundingClientRect();
    return {
      width: Math.round(box.width),
      height: Math.round(box.height),
      labels: Array.from(dialog.querySelectorAll("label")).map((el) => el.textContent),
      fields: Array.from(dialog.querySelectorAll("input,select,textarea")).map((el) => {
        const r = el.getBoundingClientRect();
        return {
          name: el.getAttribute("name"),
          x: Math.round(r.x - box.x),
          y: Math.round(r.y - box.y),
          width: Math.round(r.width),
          height: Math.round(r.height),
        };
      }),
    };
  });
}
async function footerVisible(page: Page) {
  const modal = dialogOf(page);
  await expect(modal.getByRole("button", { name: "Anuluj", exact: true })).toBeInViewport({
    ratio: 1,
  });
  await expect(modal.getByRole("button", { name: /Dodaj (inne źródło|umowę)/ })).toBeInViewport({
    ratio: 1,
  });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(await page.evaluate(() => Number.parseFloat(getComputedStyle(document.body).zoom))).toBe(
    1,
  );
}
for (const viewport of [
  { width: 1920, height: 950 },
  { width: 1440, height: 800 },
  { width: 1366, height: 650 },
  { width: 390, height: 740 },
]) {
  test(
    "both entry points have identical geometry at 100% " + viewport.width + "x" + viewport.height,
    async ({ page }) => {
      await page.setViewportSize(viewport);
      const state = await mockPeriods(page);
      state.months[3].state = "active";
      await page.goto("/");
      await page.getByRole("tab", { name: "Źródła dochodu" }).click();
      const trigger = page.getByRole("button", { name: "Dodaj źródło", exact: true });
      await trigger.click();
      const modal = dialogOf(page);
      await expect(modal).toBeVisible();
      await expect(modal.getByLabel("Rodzaj źródła")).toBeFocused();
      await footerVisible(page);
      const basicFamily = await shape(page);
      await modal.locator("summary").click();
      const expandedFamily = await shape(page);
      await footerVisible(page);
      if (viewport.width === 1920) {
        const scroll = await modal
          .locator(".source-fields")
          .evaluate((el) => ({ height: el.clientHeight, total: el.scrollHeight }));
        expect(scroll.total).toBeLessThanOrEqual(scroll.height + 1);
      }
      await modal.getByLabel("Opis").scrollIntoViewIfNeeded();
      await modal.getByLabel("Opis").hover();
      await page.mouse.wheel(0, 200);
      await expect(modal.getByLabel("Opis")).toBeInViewport({ ratio: 1 });
      await footerVisible(page);
      await page.screenshot({
        path:
          "../memory-bank/tasks/unified-source-dialog/evidence/ui-design/actual-family-" +
          viewport.width +
          ".jpg",
      });
      await page.keyboard.press("Escape");
      await expect(modal).toHaveCount(0);
      await expect(trigger).toBeFocused();
      await openMonth(page);
      await fillIncome(page);
      const source = page.getByLabel("Źródło dochodu", { exact: true });
      await source.focus();
      await source.selectOption("__create_source__");
      await expect(modal).toBeVisible();
      expect(await shape(page)).toEqual(basicFamily);
      await modal.locator("summary").click();
      expect(await shape(page)).toEqual(expandedFamily);
      await modal.getByLabel("Opis").scrollIntoViewIfNeeded();
      await modal.getByLabel("Opis").hover();
      await page.mouse.wheel(0, 200);
      await footerVisible(page);
      await page.screenshot({
        path:
          "../memory-bank/tasks/unified-source-dialog/evidence/ui-design/actual-income-" +
          viewport.width +
          ".jpg",
      });
      await page.keyboard.press("Escape");
      await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("8000,00");
      expect(state.incomes).toHaveLength(0);
    },
  );

  test(
    "contract fields scroll while footer stays visible at " + viewport.width,
    async ({ page }) => {
      await page.setViewportSize(viewport);
      const state = await mockPeriods(page);
      await page.goto("/");
      await page.getByRole("tab", { name: "Źródła dochodu" }).click();
      await page.getByRole("button", { name: "Dodaj źródło", exact: true }).click();
      const modal = dialogOf(page);
      await modal.getByLabel("Rodzaj źródła").selectOption("contract");
      await footerVisible(page);
      await modal.getByLabel("Data zakończenia umowy (opcjonalna)").scrollIntoViewIfNeeded();
      await expect(modal.getByLabel("Data zakończenia umowy (opcjonalna)")).toBeInViewport({
        ratio: 1,
      });
      await footerVisible(page);
      await page.screenshot({
        path:
          "../memory-bank/tasks/unified-source-dialog/evidence/ui-design/actual-contract-" +
          viewport.width +
          ".jpg",
      });
      await page.keyboard.press("Escape");
      expect(state.records.contracts["home-a"]).toHaveLength(1);
    },
  );
}

test("household modal saves the full source and restores its trigger", async ({ page }) => {
  const state = await mockPeriods(page);
  await page.goto("/");
  await page.getByRole("tab", { name: "Źródła dochodu" }).click();
  const trigger = page.getByRole("button", { name: "Dodaj źródło", exact: true });
  await trigger.click();
  const modal = dialogOf(page);
  await modal.getByLabel("Nazwa innego źródła").fill("Lokata wspólna");
  await modal.getByLabel("Kategoria", { exact: true }).fill("Oszczędności");
  await modal.getByLabel("Data rozpoczęcia", { exact: true }).fill("2026-01-01");
  await modal.locator("summary").click();
  await modal.getByLabel("Płatnik").fill("Bank testowy");
  await modal.getByLabel("Opcjonalna podpowiedź miesięczna").fill("100,25");
  await modal.getByLabel("Opis").fill("Syntetyczne dane");
  await modal.getByRole("button", { name: "Dodaj inne źródło", exact: true }).click();
  await expect(modal).toHaveCount(0);
  await expect(trigger).toBeFocused();
  const saved = state.records.incomes["home-a"].at(-1)!;
  expect(saved).toMatchObject({
    name: "Lokata wspólna",
    member_id: null,
    end_date: null,
    default_monthly_amount: "100.25",
    payer: "Bank testowy",
  });
  await expect(page.getByRole("row", { name: /Lokata wspólna/ })).toBeVisible();
  expect(state.incomes).toHaveLength(0);
});
