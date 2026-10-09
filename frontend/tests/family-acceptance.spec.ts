import { loginFamily as login } from "./family-live-fixture";
import { expect, test, type Page } from "@playwright/test";

const runId = process.env.FAMILY_ACCEPTANCE_RUN_ID;

async function activate(page: Page, name: string) {
  const target = page.getByRole("button", { name, exact: true });
  await target.focus();
  await page.keyboard.press("Enter");
}

async function addAgreement(
  page: Page,
  person: string,
  firm: string,
  name: string,
  hourly: boolean,
) {
  await activate(page, "Dodaj umowę");
  await expect(page.getByLabel("Osoba umowy")).toBeFocused();
  await page.getByLabel("Osoba umowy").selectOption({ label: person });
  await page.getByLabel("Nazwa umowy").fill(name);
  await page.getByLabel("Typ umowy").selectOption(hourly ? "mandate" : "employment");
  await page.getByLabel("Kwota brutto z umowy").fill(hourly ? "123,45" : "8500,25");
  await page.getByLabel("Podstawa kwoty brutto").selectOption(hourly ? "hourly" : "monthly");
  await page.getByLabel("Data rozpoczęcia umowy").fill("2026-01-01");
  if (hourly) {
    await page.getByLabel("Firma", { exact: true }).selectOption({ label: firm });
  } else {
    await activate(page, "+ Nowa firma");
    const modal = page.getByRole("dialog", { name: "Nowa firma", exact: true });
    await expect(modal.getByLabel("Nazwa firmy")).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(page.getByLabel("Firma", { exact: true })).toBeFocused();
    await activate(page, "+ Nowa firma");
    await modal.getByLabel("Nazwa firmy").fill(firm);
    await modal.getByRole("button", { name: "Dodaj firmę", exact: true }).press("Enter");
    await expect(modal).toHaveCount(0);
    await expect(page.getByLabel("Nazwa umowy")).toHaveValue(name);
    await expect(page.getByLabel("Firma", { exact: true }).locator("option:checked")).toHaveText(
      firm,
    );
  }
  await activate(page, "Dodaj umowę");
  const row = page.getByRole("row", { name: new RegExp(name) });
  await expect(row).toContainText(person);
  await expect(row).toContainText(firm);
  await expect(row).toContainText(hourly ? "123,45 PLN" : "8 500,25 PLN");
  await expect(row).toContainText(hourly ? "za godzinę" : "miesięcznie");
}

test.describe("odbiór rodziny na izolowanym rzeczywistym stosie", () => {
  test.skip(!runId, "Wymaga FAMILY_ACCEPTANCE_RUN_ID dla izolowanej instalacji.");

  for (const [role, width] of [
    ["owner", 1440],
    ["administrator", 390],
  ] as const) {
    test(`${role}: konfiguracja, edycja i archiwizacja przy ${width}px`, async ({ page }, info) => {
      await page.setViewportSize({ width, height: 900 });
      const data = await login(page, role);
      const suffix = `${role} ${runId}`;
      const person = `Osoba UI ${suffix}`;
      const firm = `Firma UI ${suffix}`;
      const first = `Umowa miesięczna ${suffix}`;
      const second = `Umowa godzinowa ${suffix}`;
      const source = `Źródło domu ${suffix}`;
      await activate(page, "Dodaj członka");
      await page.getByLabel("Nazwa członka").fill(person);
      await activate(page, "Dodaj członka");
      await expect(page.getByRole("article", { name: person, exact: true })).toBeVisible();
      await page.getByRole("tab", { name: "Członkowie" }).focus();
      await page.keyboard.press("End");
      await expect(page.getByRole("tab", { name: "Umowy" })).toBeFocused();
      await addAgreement(page, person, firm, first, false);
      await addAgreement(page, person, firm, second, true);
      await page.screenshot({ path: info.outputPath(`contracts-${width}.png`), fullPage: true });
      await page.getByRole("tab", { name: "Umowy" }).focus();
      await page.keyboard.press("ArrowLeft");
      await expect(page.getByRole("tab", { name: "Źródła dochodu" })).toBeFocused();
      await activate(page, "Dodaj źródło");
      await expect(page.getByLabel("Przypisz źródło do")).toBeFocused();
      await page.getByLabel("Nazwa innego źródła").fill(source);
      await page.getByLabel("Kategoria").fill("inne");
      await page.getByLabel("Data rozpoczęcia", { exact: true }).fill("2026-01-01");
      await activate(page, "Dodaj inne źródło");
      const row = page.getByRole("row", { name: new RegExp(source) });
      await expect(
        page.getByRole("region", { name: "Źródła całego gospodarstwa — tabela", exact: true }),
      ).toContainText(source);
      await expect(row).toContainText("Brak podpowiedzi");
      await row.getByRole("button", { name: "Edytuj", exact: true }).press("Enter");
      await page.getByLabel("Nazwa innego źródła").fill(`${source} zmienione`);
      await activate(page, "Zapisz inne źródło");
      await page
        .getByRole("row", { name: new RegExp(source) })
        .getByRole("button", { name: "Edytuj", exact: true })
        .press("Enter");
      page.once("dialog", (dialog) => dialog.accept());
      await activate(page, "Archiwizuj źródło");
      await expect(page.getByRole("row", { name: new RegExp(source) })).toContainText("Archiwalne");
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
        width,
      );
      expect(
        await page.evaluate(() =>
          getComputedStyle(document.documentElement).getPropertyValue("--color-background").trim(),
        ),
      ).toBe("#f5f6f2");
      await page.screenshot({ path: info.outputPath(`sources-${width}.png`), fullPage: true });
      if (role === "owner") {
        await page.getByLabel("Aktywne gospodarstwo").selectOption(data.households[1]);
        await page.getByRole("tab", { name: "Członkowie" }).click();
        await expect(page.getByRole("article", { name: person, exact: true })).toHaveCount(0);
        await expect(
          page.getByRole("article", { name: `Osoba historyczna B ${runId}`, exact: true }),
        ).toBeVisible();
      }
    });
  }

  for (const role of ["member", "viewer"]) {
    test(`${role}: odczyt bez akcji zapisu`, async ({ page }) => {
      await login(page, role);
      for (const section of ["Członkowie", "Źródła dochodu", "Umowy"]) {
        await page.getByRole("tab", { name: section }).click();
        await expect(
          page.getByRole("button", { name: /Dodaj|Edytuj|Archiwizuj|Przekształć|Dezaktywuj/ }),
        ).toHaveCount(0);
      }
      await expect(
        page.getByRole("row", { name: new RegExp(`Umowa miesięczna owner ${runId}`) }),
      ).toBeVisible();
    });
  }

  test("jawna konwersja historycznego wynagrodzenia zachowuje UUID", async ({ page }) => {
    const data = await login(page, "owner");
    await page.getByRole("tab", { name: "Źródła dochodu" }).click();
    await page
      .getByRole("row", { name: /Wynagrodzenie/ })
      .getByRole("button", { name: "Przekształć w umowę", exact: true })
      .click();
    await expect(
      page.getByText("Ta operacja nie doda przychodu za miesiąc.", { exact: false }),
    ).toBeVisible();
    await page
      .getByLabel("Firma", { exact: true })
      .selectOption({ label: `Firma UI owner ${runId}` });
    await page.getByLabel("Kwota brutto z umowy").fill("1234,56");
    const converted = page.waitForResponse(
      (response) =>
        response.url().endsWith(`/income-sources/${data.salary}/convert-to-contract/`) &&
        response.request().method() === "POST",
    );
    await activate(page, "Przekształć w umowę");
    const response = await converted;
    expect(response.status()).toBe(200);
    expect(await response.json()).toMatchObject({
      id: data.salary,
      version: 2,
      gross_amount: "1234.56",
    });
    await expect(page.getByRole("row", { name: /Wynagrodzenie/ })).toContainText("1 234,56 PLN");
  });
});
