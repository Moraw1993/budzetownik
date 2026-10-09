import { expect, test } from "@playwright/test";
import { fillIncome, mockPeriods, openMonth } from "./period-fixtures";

for (const width of [1440, 390]) {
  test("source modal preserves income draft, files and focus at " + width, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const state = await mockPeriods(page);
    state.months[3].state = "active";
    await openMonth(page);
    await fillIncome(page);
    await page.getByLabel("Typ odbiorcy").selectOption("member");
    await page.getByLabel("Osoba", { exact: true }).selectOption("member-1");
    await page.getByLabel("Źródło dochodu", { exact: true }).selectOption("contract-1");
    const source = page.getByLabel("Źródło dochodu", { exact: true });
    const original = await source.inputValue();
    await page.getByLabel("Opcjonalne załączniki (PNG, JPG, PDF)").setInputFiles({
      name: "szkic.png",
      mimeType: "image/png",
      buffer: Buffer.from("synthetic"),
    });
    const top = await page
      .getByLabel("Faktyczna kwota przychodu")
      .evaluate((e) => e.getBoundingClientRect().top + window.scrollY);
    await source.focus();
    await source.selectOption("__create_source__");
    const dialog = page.getByRole("dialog", { name: "Nowe źródło dochodu" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByLabel("Rodzaj źródła")).toBeFocused();
    await expect(dialog.getByLabel("Przypisz źródło do")).toHaveValue("member-1");
    await expect(dialog.getByLabel("Data rozpoczęcia", { exact: true })).toHaveValue("2026-04-01");
    await expect(dialog.getByLabel("Płatnik")).toBeHidden();
    expect(await source.inputValue()).toBe(original);
    const box = await dialog.boundingBox();
    expect(box!.width).toBeLessThanOrEqual(width - 24);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    await page.screenshot({
      path:
        "../memory-bank/tasks/income-source-dialog/evidence/ui-design/actual-other-" +
        width +
        ".jpg",
    });
    await page.keyboard.press("Shift+Tab");
    expect(await dialog.evaluate((e) => e.contains(document.activeElement))).toBe(true);
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(source).toBeFocused();
    expect(
      await page
        .getByLabel("Faktyczna kwota przychodu")
        .evaluate((e) => e.getBoundingClientRect().top + window.scrollY),
    ).toBe(top);
    await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("8000,00");
    await expect(page.getByLabel("Data otrzymania")).toHaveValue("2026-03-30");
    expect(
      await page
        .getByLabel("Opcjonalne załączniki (PNG, JPG, PDF)")
        .evaluate((e: HTMLInputElement) => e.files?.[0]?.name),
    ).toBe("szkic.png");
    await source.selectOption("__create_source__");
    await dialog.getByLabel("Nazwa innego źródła").fill("Odsetki");
    await page.keyboard.press("Escape");
    await expect(dialog.getByRole("heading", { name: "Odrzucić szkic źródła?" })).toBeVisible();
    expect(
      await dialog.getByLabel("Nazwa innego źródła").evaluate((e) => !!e.closest("[inert]")),
    ).toBe(true);
    await page.keyboard.press("Escape");
    await expect(dialog.getByLabel("Nazwa innego źródła")).toHaveValue("Odsetki");
    await dialog.getByRole("button", { name: "Anuluj", exact: true }).click();
    await dialog.getByRole("button", { name: "Odrzuć szkic źródła", exact: true }).click();
    await expect(dialog).toHaveCount(0);
    expect(state.incomes).toHaveLength(0);
    expect(state.records.incomes["home-a"]).toHaveLength(2);
  });

  test(
    "contract modal keeps optional end and draft while adding company at " + width,
    async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      const state = await mockPeriods(page);
      state.months[3].state = "active";
      await openMonth(page);
      await fillIncome(page);
      await page.getByLabel("Typ odbiorcy").selectOption("member");
      await page.getByLabel("Osoba", { exact: true }).selectOption("member-1");
      await page.getByLabel("Źródło dochodu", { exact: true }).selectOption("contract-1");
      await page.getByLabel("Źródło dochodu", { exact: true }).focus();
      await page.getByLabel("Źródło dochodu", { exact: true }).selectOption("__create_source__");
      const dialog = page.getByRole("dialog", { name: "Nowe źródło dochodu" });
      await dialog.getByLabel("Rodzaj źródła").selectOption("contract");
      await expect(dialog.getByLabel("Osoba umowy")).toHaveValue("member-1");
      await dialog.getByLabel("Nazwa umowy").fill("Wynagrodzenie dodatkowe");
      await dialog.getByLabel("Kwota brutto z umowy").fill("10000,25");
      await dialog.getByRole("button", { name: "+ Nowa firma", exact: true }).click();
      const company = page.getByRole("dialog", { name: "Nowa firma", exact: true });
      await expect(company.getByLabel("Nazwa firmy")).toBeFocused();
      await page.keyboard.press("Escape");
      await expect(company).toHaveCount(0);
      await expect(dialog.getByLabel("Firma", { exact: true })).toBeFocused();
      await expect(dialog.getByLabel("Nazwa umowy")).toHaveValue("Wynagrodzenie dodatkowe");
      await dialog.getByLabel("Firma", { exact: true }).selectOption("company-1");
      const end = dialog.getByLabel("Data zakończenia umowy (opcjonalna)");
      await expect(end).not.toHaveAttribute("required");
      await expect(end).toHaveAccessibleDescription(
        "Puste pole oznacza umowę na czas nieokreślony.",
      );
      await end.scrollIntoViewIfNeeded();
      await page.screenshot({
        path:
          "../memory-bank/tasks/income-source-dialog/evidence/ui-design/actual-contract-" +
          width +
          ".jpg",
      });
      await dialog.getByRole("button", { name: "Dodaj umowę", exact: true }).click();
      await expect(dialog).toHaveCount(0);
      const saved = state.records.contracts["home-a"].at(-1)!;
      expect(saved.end_date).toBeNull();
      expect(saved.member_id).toBe("member-1");
      expect(saved.gross_amount).toBe("10000.25");
      expect(state.incomes).toHaveLength(0);
      await expect(page.getByLabel("Faktyczna kwota przychodu")).toHaveValue("8000,00");
    },
  );
}

test("hidden field API errors expand details without dropping source or income", async ({
  page,
}) => {
  const state = await mockPeriods(page);
  state.months[3].state = "active";
  await openMonth(page);
  await fillIncome(page);
  await page.getByLabel("Źródło dochodu", { exact: true }).selectOption("__create_source__");
  const dialog = page.getByRole("dialog", { name: "Nowe źródło dochodu" });
  await dialog.getByLabel("Nazwa innego źródła").fill("Odsetki");
  await dialog.getByLabel("Kategoria", { exact: true }).fill("Oszczędności");
  await page.route("**/income-sources/", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    expect(route.request().postDataJSON().end_date).toBeNull();
    return route.fulfill({ status: 400, json: { payer: ["Sprawdź płatnika."] } });
  });
  await dialog.getByRole("button", { name: "Dodaj inne źródło", exact: true }).click();
  await expect(dialog.getByLabel("Płatnik")).toBeVisible();
  await expect(dialog.getByText("Sprawdź płatnika.", { exact: true })).toBeVisible();
  await expect(dialog.getByLabel("Nazwa innego źródła")).toHaveValue("Odsetki");
  expect(state.incomes).toHaveLength(0);
});
