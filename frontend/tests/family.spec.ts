import { expect, test, type Page } from "@playwright/test";
import { company, contract, contractSource, income, member, mockRecords } from "./record-fixtures";

async function openContract(page: Page) {
  await page.getByRole("tab", { name: "Umowy" }).click();
  await page.getByRole("button", { name: "Dodaj umowę", exact: true }).click();
}

async function fillContract(page: Page, name = "Nowa umowa") {
  await page.getByLabel("Osoba umowy").selectOption("member-1");
  await page.getByLabel("Firma", { exact: true }).selectOption("company-1");
  await page.getByLabel("Nazwa umowy").fill(name);
  await page.getByLabel("Kwota brutto z umowy").fill("1234567890123456,78");
  await page.getByLabel("Data rozpoczęcia umowy").fill("2026-01-01");
}

function familyData() {
  const firm = company();
  const agreement = contract("contract-1", "member-1", firm);
  return {
    members: [member("member-1", "Anna"), member("member-2", "Jan")],
    companies: [firm],
    contracts: [agreement],
    incomes: [
      income("income-1", "member-1"),
      { ...income("income-home"), name: "Najem gospodarstwa" },
      contractSource(agreement),
    ],
  };
}

test("kontrolki pierwszego rzędu formularza umowy mają równe wymiary", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const state = await mockRecords(page, {
    members: [member("member-1", "Anna")],
    companies: [company("long-company", "Firma o bardzo długiej nazwie testowej")],
  });
  await page.goto("/");
  await openContract(page);
  await page.getByLabel("Firma", { exact: true }).selectOption("long-company");
  await page.evaluate(() => document.fonts.ready);

  await page.screenshot({
    path: testInfo.outputPath("contract-form-1440.png"),
    fullPage: true,
  });

  const controlBoxes = await page.evaluate(() =>
    [
      "#contract-form select[name='member_id']",
      "#contract-form select[name='company_id']",
      "#contract-form input[name='name']",
    ].map((selector) => {
      const bounds = document.querySelector(selector)?.getBoundingClientRect();
      return bounds ? { y: bounds.y, height: bounds.height } : null;
    }),
  );
  expect(controlBoxes.every(Boolean)).toBe(true);
  const [memberBox, companyBox, nameBox] = controlBoxes;
  expect(Math.abs(memberBox!.y - companyBox!.y)).toBeLessThanOrEqual(1);
  expect(Math.abs(nameBox!.y - companyBox!.y)).toBeLessThanOrEqual(1);
  expect(Math.abs(memberBox!.height - companyBox!.height)).toBeLessThanOrEqual(1);
  expect(Math.abs(nameBox!.height - companyBox!.height)).toBeLessThanOrEqual(1);
  expect(memberBox!.height).toBeGreaterThanOrEqual(44);
  expect(companyBox!.height).toBeGreaterThanOrEqual(44);
  expect(nameBox!.height).toBeGreaterThanOrEqual(44);

  const initialRowBounds = await page.evaluate(() => {
    const companyButton = document
      .querySelector<HTMLButtonElement>("#contract-form .company-select-field > .button")
      ?.getBoundingClientRect();
    const nextRow = document
      .querySelector<HTMLSelectElement>("#contract-form select[name='contract_type']")
      ?.getBoundingClientRect();
    return companyButton && nextRow
      ? { buttonBottom: companyButton.bottom, nextRowTop: nextRow.top }
      : null;
  });
  expect(initialRowBounds).not.toBeNull();
  expect(initialRowBounds!.buttonBottom).toBeLessThan(initialRowBounds!.nextRowTop);

  await page.getByLabel("Osoba umowy").selectOption("member-1");
  await page.getByLabel("Nazwa umowy").fill("Umowa walidacyjna");
  await page.getByLabel("Kwota brutto z umowy").fill("1234,56");
  await page.getByLabel("Data rozpoczęcia umowy").fill("2026-01-01");
  state.rejectWrite = {
    status: 400,
    body: { member_id: ["Błąd walidacji osoby umowy."] },
  };
  await page.getByRole("button", { name: "Dodaj umowę", exact: true }).click();
  await expect(page.getByLabel("Osoba umowy")).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByLabel("Osoba umowy")).toHaveAccessibleDescription(
    "Błąd walidacji osoby umowy.",
  );
  await page.screenshot({
    path: testInfo.outputPath("contract-form-1440-validation.png"),
    fullPage: true,
  });
  const errorRowBounds = await page.evaluate(() => {
    const companyButton = document
      .querySelector<HTMLButtonElement>("#contract-form .company-select-field > .button")
      ?.getBoundingClientRect();
    const nextRow = document
      .querySelector<HTMLSelectElement>("#contract-form select[name='contract_type']")
      ?.getBoundingClientRect();
    return companyButton && nextRow
      ? { buttonBottom: companyButton.bottom, nextRowTop: nextRow.top }
      : null;
  });
  expect(errorRowBounds).not.toBeNull();
  expect(errorRowBounds!.buttonBottom).toBeLessThan(errorRowBounds!.nextRowTop);
});

test("karty, zakładki, przypisania i liczniki nie mieszają typów źródeł", async ({ page }) => {
  await mockRecords(page, familyData());
  await page.goto("/");
  await expect(page.getByRole("article", { name: "Anna", exact: true })).toContainText(
    "Wynagrodzenie",
  );
  await expect(page.getByRole("article", { name: "Anna", exact: true })).toContainText(
    "Umowa podstawowa",
  );
  await expect(page.getByRole("article", { name: "Jan", exact: true })).toContainText(
    "Nie przypisano źródeł",
  );
  await expect(page.getByRole("tab", { name: "Członkowie" })).toContainText("2");
  await expect(page.getByRole("tab", { name: "Źródła dochodu" })).toContainText("2");
  await expect(page.getByRole("tab", { name: "Umowy" })).toContainText("1");
  await expect(page.getByRole("tabpanel").locator("form")).toHaveCount(0);
  await page.getByRole("tab", { name: "Źródła dochodu" }).click();
  await expect(
    page.getByRole("region", { name: "Inne źródła osób — tabela", exact: true }),
  ).toContainText("Anna");
  await expect(
    page.getByRole("region", { name: "Źródła całego gospodarstwa — tabela", exact: true }),
  ).toContainText("Najem gospodarstwa");
  await expect(page.getByRole("row", { name: /Umowa podstawowa/ })).toHaveCount(0);
  await page.getByRole("tab", { name: "Umowy" }).click();
  await expect(page.getByRole("row", { name: /Umowa podstawowa/ })).toContainText("7 500,25 PLN");
  await expect(page.getByRole("row", { name: /Wynagrodzenie/ })).toHaveCount(0);
});

for (const role of ["owner", "administrator"] as const) {
  test(`${role} dodaje firmę w modalu bez utraty umowy i precyzji kwoty`, async ({ page }) => {
    const state = await mockRecords(page, {
      role,
      members: [member("member-1", "Anna")],
      companies: [company()],
    });
    await page.goto("/");
    await openContract(page);
    await expect(page.getByLabel("Osoba umowy")).toBeFocused();
    await fillContract(page);
    await page.getByRole("button", { name: "+ Nowa firma", exact: true }).click();
    const dialog = page.getByRole("dialog", { name: "Nowa firma", exact: true });
    await expect(dialog.getByLabel("Nazwa firmy")).toBeFocused();
    await dialog.getByLabel("Nazwa firmy").fill("Nowy pracodawca");
    await dialog.getByRole("button", { name: "Dodaj firmę" }).click();
    await expect(dialog).toHaveCount(0);
    await expect(page.getByLabel("Nazwa umowy")).toHaveValue("Nowa umowa");
    await expect(page.getByLabel("Firma", { exact: true })).toHaveValue("companies-2");
    await expect(page.getByLabel("Firma", { exact: true })).toBeFocused();
    await page.getByRole("button", { name: "Dodaj umowę", exact: true }).click();
    await expect(page.getByRole("row", { name: /Nowa umowa/ })).toContainText(
      "1 234 567 890 123 456,78 PLN",
    );
    expect(
      state.requests.find((item) => item.path.endsWith("/contracts/") && item.method === "POST")
        ?.body,
    ).toMatchObject({
      company_id: "companies-2",
      member_id: "member-1",
      gross_amount: "1234567890123456.78",
      gross_basis: "monthly",
    });
    expect(state.requests.filter((item) => item.method !== "GET").map((item) => item.path)).toEqual(
      ["/api/households/home-a/companies/", "/api/households/home-a/contracts/"],
    );
  });
}

test("typ umowy steruje polami, Escape zachowuje formularz", async ({ page }) => {
  await mockRecords(page, {
    members: [member("member-1", "Anna")],
    companies: [company(), company("archived-company", "Archiwalna firma", false)],
  });
  await page.goto("/");
  await openContract(page);
  await fillContract(page);
  await expect(page.getByLabel("Firma", { exact: true }).locator("option")).toHaveCount(2);
  await page.getByLabel("Typ umowy").selectOption("mandate");
  await expect(page.getByLabel("Stanowisko", { exact: true })).toBeVisible();
  await page.getByLabel("Typ umowy").selectOption("specific_work");
  await expect(page.getByLabel("Stanowisko", { exact: true })).toHaveCount(0);
  await page.getByLabel("Typ umowy").selectOption("other");
  await expect(page.getByLabel("Własna nazwa typu umowy")).toBeVisible();
  await page.getByLabel("Własna nazwa typu umowy").fill("Licencja");
  await page.getByRole("button", { name: "+ Nowa firma" }).click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByLabel("Nazwa umowy")).toHaveValue("Nowa umowa");
  await expect(page.getByLabel("Firma", { exact: true })).toBeFocused();
});

test("błąd walidacji API trafia pod pole i zachowuje dane umowy", async ({ page }) => {
  const state = await mockRecords(page, {
    members: [member("member-1", "Anna")],
    companies: [company()],
  });
  await page.goto("/");
  await openContract(page);
  await fillContract(page);
  state.rejectWrite = {
    status: 400,
    body: { gross_amount: ["Kwota przekracza dopuszczalny zakres."] },
  };
  await page.getByRole("button", { name: "Dodaj umowę", exact: true }).click();
  await expect(page.getByLabel("Kwota brutto z umowy")).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByLabel("Kwota brutto z umowy")).toHaveAccessibleDescription(
    "Kwota przekracza dopuszczalny zakres.",
  );
  await expect(page.getByLabel("Nazwa umowy")).toHaveValue("Nowa umowa");
  expect(state.contracts["home-a"]).toHaveLength(0);
});

for (const role of ["member", "viewer"] as const) {
  test(`${role} odczytuje umowy i firmy bez akcji zapisu`, async ({ page }) => {
    await mockRecords(page, { ...familyData(), role });
    await page.goto("/");
    await page.getByRole("tab", { name: "Umowy" }).click();
    await expect(page.getByRole("row", { name: /Umowa podstawowa/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dodaj|Edytuj|Archiwizuj/ })).toHaveCount(0);
    await page.getByRole("button", { name: "Zarządzaj firmami" }).click();
    await expect(page.getByRole("row", { name: /Firma testowa/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dodaj|Edytuj|Archiwizuj/ })).toHaveCount(0);
  });
}

test("źródło gospodarstwa bez kwoty i jednorazowa częstotliwość", async ({ page }) => {
  const state = await mockRecords(page);
  await page.goto("/");
  await page.getByRole("tab", { name: "Źródła dochodu" }).click();
  await page.getByRole("button", { name: "Dodaj źródło" }).click();
  await expect(page.getByLabel("Rodzaj źródła")).toBeFocused();
  await page.getByLabel("Nazwa innego źródła").fill("Sprzedaż roweru");
  await page.getByLabel("Kategoria").fill("sprzedaż");
  await page.getByLabel("Częstotliwość").selectOption("one_off");
  await expect(page.getByLabel("Źródło regularne")).toBeDisabled();
  await page.getByLabel("Data rozpoczęcia", { exact: true }).fill("2026-09-29");
  await page.getByRole("button", { name: "Dodaj inne źródło", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Źródła całego gospodarstwa — tabela", exact: true }),
  ).toContainText("Sprzedaż roweru");
  await expect(page.getByRole("row", { name: /Sprzedaż roweru/ })).toContainText(
    "Brak podpowiedzi",
  );
  expect(state.incomes["home-a"][0]).toMatchObject({
    member_id: null,
    default_monthly_amount: null,
    is_regular: false,
    frequency: "one_off",
    kind: "other",
  });
});

test("jawna konwersja zachowuje ID i wersję bez zapisu przychodu miesiąca", async ({ page }) => {
  const state = await mockRecords(page, {
    members: [member("member-1", "Anna")],
    incomes: [income("legacy-source", "member-1")],
    companies: [company()],
  });
  await page.goto("/");
  await page.getByRole("tab", { name: "Źródła dochodu" }).click();
  expect(state.incomes["home-a"][0].kind).toBe("other");
  await page.getByRole("button", { name: "Przekształć w umowę", exact: true }).click();
  await expect(page.getByRole("tab", { name: "Umowy" })).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByText("Ta operacja nie doda przychodu za miesiąc.", { exact: false }),
  ).toBeVisible();
  await expect(page.getByLabel("Nazwa umowy")).toHaveValue("Wynagrodzenie");
  await fillContract(page, "Umowa po konwersji");
  await page.getByRole("button", { name: "Przekształć w umowę", exact: true }).click();
  await expect(page.getByRole("row", { name: /Umowa po konwersji/ })).toBeVisible();
  expect(state.incomes["home-a"]).toHaveLength(1);
  expect(state.incomes["home-a"][0]).toMatchObject({
    id: "legacy-source",
    kind: "contract",
    version: 2,
    default_monthly_amount: null,
  });
  const writes = state.requests.filter((item) => item.method !== "GET");
  expect(writes).toHaveLength(1);
  expect(writes[0]).toMatchObject({
    path: "/api/households/home-a/income-sources/legacy-source/convert-to-contract/",
    body: { expected_version: 1 },
  });
});

for (const operation of ["other", "contract", "conversion"] as const) {
  test(`konflikt wersji ${operation} zamyka edycję i odświeża dane`, async ({ page }) => {
    const state = await mockRecords(page, familyData());
    await page.goto("/");
    if (operation === "contract") {
      await page.getByRole("tab", { name: "Umowy" }).click();
      await page
        .getByRole("row", { name: /Umowa podstawowa/ })
        .getByRole("button", { name: "Edytuj" })
        .click();
    } else {
      await page.getByRole("tab", { name: "Źródła dochodu" }).click();
      await page
        .getByRole("row", { name: /Wynagrodzenie/ })
        .getByRole("button", {
          name: operation === "other" ? "Edytuj" : "Przekształć w umowę",
          exact: true,
        })
        .click();
      if (operation === "conversion") await fillContract(page);
    }
    const readsBefore = state.requests.filter(
      (item) => item.method === "GET" && item.path.endsWith("/income-sources/"),
    ).length;
    state.rejectWrite = { status: 409, body: { code: "source_conflict" } };
    const submit =
      operation === "other"
        ? "Zapisz inne źródło"
        : operation === "contract"
          ? "Zapisz umowę"
          : "Przekształć w umowę";
    await page.getByRole("button", { name: submit, exact: true }).click();
    await expect(page.getByRole("tabpanel").getByRole("alert")).toContainText(
      operation === "other" ? "wybierz je ponownie" : "wybierz rekord ponownie",
    );
    await expect(
      page.getByLabel(operation === "other" ? "Nazwa innego źródła" : "Nazwa umowy"),
    ).toHaveCount(0);
    await expect
      .poll(
        () =>
          state.requests.filter(
            (item) => item.method === "GET" && item.path.endsWith("/income-sources/"),
          ).length,
      )
      .toBeGreaterThan(readsBefore);
    expect(
      state.requests.filter((item) => item.method !== "GET").at(-1)?.body?.expected_version,
    ).toBe(1);
  });
}

test("edycja i archiwizacja umowy oraz słownika firm", async ({ page }) => {
  const state = await mockRecords(page, familyData());
  await page.goto("/");
  await page.getByRole("tab", { name: "Umowy" }).click();
  await page
    .getByRole("row", { name: /Umowa podstawowa/ })
    .getByRole("button", { name: "Edytuj" })
    .click();
  await page.getByLabel("Nazwa umowy").fill("Umowa zmieniona");
  await page.getByRole("button", { name: "Zapisz umowę" }).click();
  await page
    .getByRole("row", { name: /Umowa zmieniona/ })
    .getByRole("button", { name: "Edytuj" })
    .click();
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Archiwizuj umowę" }).click();
  await expect(page.getByRole("row", { name: /Umowa zmieniona/ })).toContainText("Archiwalna");
  await expect(page.getByRole("row", { name: /Umowa zmieniona/ }).getByRole("button")).toHaveCount(
    0,
  );
  expect(state.contracts["home-a"][0].version).toBe(2);
  await page.getByRole("button", { name: "Zarządzaj firmami" }).click();
  await page
    .getByRole("row", { name: /Firma testowa/ })
    .getByRole("button", { name: "Edytuj" })
    .click();
  await page.getByLabel("Nazwa firmy").fill("Firma zmieniona");
  await page.getByRole("button", { name: "Zapisz firmę" }).click();
  await expect(page.getByRole("row", { name: /Firma zmieniona/ })).toBeVisible();
  page.once("dialog", (dialog) => dialog.accept());
  await page
    .getByRole("row", { name: /Firma zmieniona/ })
    .getByRole("button", { name: "Archiwizuj", exact: true })
    .click();
  await expect(page.getByRole("row", { name: /Firma zmieniona/ })).toContainText("Archiwalna");
  await expect(page.getByRole("row", { name: /Firma zmieniona/ }).getByRole("button")).toHaveCount(
    0,
  );
});

for (const width of [1440, 1024, 390]) {
  test(`jasny design, klawiatura i przewijanie tabel przy ${width}px`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await mockRecords(page, familyData());
    await page.goto("/");
    await expect(page.getByRole("article", { name: "Anna", exact: true })).toBeVisible();
    expect(
      await page.evaluate(() =>
        getComputedStyle(document.documentElement).getPropertyValue("--color-background").trim(),
      ),
    ).toBe("#f5f6f2");
    const membersTab = page.getByRole("tab", { name: "Członkowie" });
    await membersTab.focus();
    await page.keyboard.press("ArrowRight");
    await expect(page.getByRole("tab", { name: "Źródła dochodu" })).toBeFocused();
    await expect(page.getByRole("tabpanel")).toHaveAccessibleName(/Źródła dochodu/);
    await page.keyboard.press("End");
    await expect(page.getByRole("tab", { name: "Umowy" })).toBeFocused();
    await page.keyboard.press("Home");
    await expect(membersTab).toBeFocused();
    for (const section of ["Członkowie", "Źródła dochodu", "Umowy"]) {
      await page.getByRole("tab", { name: section }).click();
      if (section === "Umowy")
        await expect(page.getByRole("row", { name: /Umowa podstawowa/ })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
        width,
      );
      await page.screenshot({
        path: testInfo.outputPath(`${section}-${width}.png`),
        fullPage: true,
      });
      if (section !== "Członkowie" && width <= 1024) {
        const table = page.getByRole("region", {
          name: section === "Umowy" ? "Umowy — tabela" : "Inne źródła osób — tabela",
          exact: true,
        });
        expect(await table.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(
          true,
        );
        await table.focus();
        await page.keyboard.press("ArrowRight");
        await expect.poll(() => table.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
      }
    }
    await page.getByRole("button", { name: "Dodaj umowę", exact: true }).click();
    await expect(page.getByLabel("Osoba umowy")).toBeFocused();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      width,
    );
    await page.screenshot({
      path: testInfo.outputPath(`contract-form-${width}.png`),
      fullPage: true,
    });
    await page.getByRole("button", { name: "+ Nowa firma" }).click();
    await expect(page.getByRole("dialog").getByLabel("Nazwa firmy")).toBeFocused();
    const dialogBox = await page.getByRole("dialog").boundingBox();
    expect(dialogBox!.x).toBeGreaterThanOrEqual(0);
    expect(dialogBox!.x + dialogBox!.width).toBeLessThanOrEqual(width);
    await page.keyboard.press("Escape");
    await expect(page.getByLabel("Firma", { exact: true })).toBeFocused();
    await page.getByRole("tab", { name: "Źródła dochodu" }).click();
    await page.getByRole("button", { name: "Dodaj źródło", exact: true }).click();
    await expect(page.getByLabel("Rodzaj źródła")).toBeFocused();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      width,
    );
    await page.screenshot({
      path: testInfo.outputPath(`form-source-${width}.png`),
      fullPage: true,
    });
  });
}
