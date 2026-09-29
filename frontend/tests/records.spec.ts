import { expect, test } from "@playwright/test";
import { income, member, mockRecords, relation } from "./record-fixtures";

test("Owner dodaje relację, członka i źródło bez utraty precyzji", async ({ page }) => {
  const state = await mockRecords(page);
  await page.goto("/");
  await expect(page.getByText("Brak członków.", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Relacje rodzinne", exact: true }).click();
  await page.getByRole("button", { name: "Dodaj relację", exact: true }).click();
  await page.getByLabel("Nazwa relacji").fill("Rodzic");
  await page.getByRole("button", { name: "Dodaj relację", exact: true }).click();
  await expect(page.locator(".record-list strong", { hasText: "Rodzic" })).toBeVisible();
  await page.getByRole("button", { name: "Wróć do członków" }).click();
  await page.getByRole("button", { name: "Dodaj członka", exact: true }).click();
  await page.getByLabel("Nazwa członka").fill("Anna");
  await page.getByLabel("Relacja rodzinna").selectOption({ label: "Rodzic" });
  await page.getByLabel("Powiązane konto").selectOption({ label: "arek" });
  await page.getByRole("button", { name: "Dodaj członka", exact: true }).click();
  await expect(page.getByRole("article", { name: "Anna", exact: true })).toContainText("Rodzic");
  await expect(page.getByRole("article", { name: "Anna", exact: true })).toContainText("arek");
  await page.getByRole("tab", { name: "Źródła dochodu" }).click();
  await page.getByRole("button", { name: "Dodaj źródło", exact: true }).click();
  await page.getByLabel("Przypisz źródło do").selectOption({ label: "Anna" });
  await page.getByLabel("Nazwa innego źródła").fill("Stypendium");
  await page.getByLabel("Kategoria").fill("nauka");
  await page.getByLabel("Płatnik").fill("Uczelnia");
  await page.getByLabel("Częstotliwość").selectOption("weekly");
  await page.getByLabel("Data rozpoczęcia", { exact: true }).fill("2026-01-01");
  await page.getByLabel("Data zakończenia", { exact: true }).fill("2026-12-31");
  await page.getByLabel("Opcjonalna podpowiedź miesięczna").fill("1234567890123456,78");
  await page.getByLabel("Waluta", { exact: true }).fill("eur");
  await page.getByLabel("Źródło regularne").uncheck();
  await page.getByLabel("Opis").fill("Kwota planistyczna");
  await page.getByRole("button", { name: "Dodaj inne źródło", exact: true }).click();
  await expect(page.getByRole("row", { name: /Stypendium/ })).toContainText(
    "1 234 567 890 123 456,78 EUR",
  );
  expect(
    state.requests.find((item) => item.path.endsWith("/income-sources/") && item.method === "POST")
      ?.body,
  ).toMatchObject({
    member_id: "members-1",
    default_monthly_amount: "1234567890123456.78",
    currency: "EUR",
    frequency: "weekly",
    is_regular: false,
    end_date: "2026-12-31",
  });
});

test("edycja i archiwizacja zachowują członka i źródło", async ({ page }) => {
  await mockRecords(page, {
    members: [member("member-1", "Anna")],
    incomes: [income("income-1", "member-1")],
  });
  await page.goto("/");
  await page
    .getByRole("article", { name: "Anna", exact: true })
    .getByRole("button", { name: "Edytuj" })
    .click();
  await page.getByLabel("Nazwa członka").fill("Anna Kowalska");
  await page.getByRole("button", { name: "Zapisz członka" }).click();
  await page
    .getByRole("article", { name: "Anna Kowalska" })
    .getByRole("button", { name: "Edytuj" })
    .click();
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.getByRole("button", { name: "Dezaktywuj członka" }).click();
  await expect(page.getByLabel("Nazwa członka")).toHaveValue("Anna Kowalska");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Dezaktywuj członka" }).click();
  await expect(page.getByRole("article", { name: "Anna Kowalska" })).toContainText("Archiwalny");
  await expect(
    page.getByRole("article", { name: "Anna Kowalska" }).getByRole("button"),
  ).toHaveCount(0);
  await page.getByRole("tab", { name: "Źródła dochodu" }).click();
  await page
    .getByRole("row", { name: /Wynagrodzenie/ })
    .getByRole("button", { name: "Edytuj" })
    .click();
  await expect(page.getByLabel("Przypisz źródło do")).toHaveValue("member-1");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Archiwizuj źródło" }).click();
  await expect(page.getByRole("row", { name: /Wynagrodzenie/ })).toContainText("Archiwalne");
  await expect(page.getByRole("row", { name: /Wynagrodzenie/ }).getByRole("button")).toHaveCount(0);
});

for (const role of ["member", "viewer"] as const) {
  test(`${role} widzi członków i źródła bez akcji zapisu`, async ({ page }) => {
    await mockRecords(page, {
      role,
      members: [member("member-1", "Anna")],
      incomes: [income("income-1", "member-1")],
    });
    await page.goto("/");
    await expect(page.getByRole("article", { name: "Anna" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dodaj|Edytuj|Dezaktywuj/ })).toHaveCount(0);
    await page.getByRole("tab", { name: "Źródła dochodu" }).click();
    await expect(page.getByRole("row", { name: /Wynagrodzenie/ })).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Dodaj|Edytuj|Archiwizuj|Przekształć/ }),
    ).toHaveCount(0);
  });
}

test("Administrator zapisuje, odmowa API odświeża rolę", async ({ page }) => {
  const state = await mockRecords(page, { role: "administrator" });
  await page.goto("/");
  await page.getByRole("button", { name: "Dodaj członka", exact: true }).click();
  await page.getByLabel("Nazwa członka").fill("Osoba admina");
  await page.getByRole("button", { name: "Dodaj członka", exact: true }).click();
  await expect(page.getByRole("article", { name: "Osoba admina" })).toBeVisible();
  await page.getByRole("button", { name: "Dodaj członka", exact: true }).click();
  state.denyNextWrite = true;
  await page.getByLabel("Nazwa członka").fill("Odrzucona osoba");
  await page.getByRole("button", { name: "Dodaj członka", exact: true }).click();
  await expect(page.getByText("Tryb odczytu. Członków", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Dodaj członka" })).toHaveCount(0);
  expect(state.members["home-a"].some((item) => item.display_name === "Odrzucona osoba")).toBe(
    false,
  );
});

test("paginacja członków i pełny słownik relacji", async ({ page }) => {
  await mockRecords(page, {
    members: Array.from({ length: 51 }, (_, i) => member(`member-${i}`, `Osoba ${i}`)),
    relations: Array.from({ length: 51 }, (_, i) => relation(`relation-${i}`, `Relacja ${i}`)),
  });
  await page.goto("/");
  await expect(page.getByText("Strona 1 z 2")).toBeVisible();
  await page.getByRole("button", { name: "Następna" }).click();
  await expect(page.getByRole("article", { name: "Osoba 50", exact: true })).toBeVisible();
  await expect(page.getByText("Strona 2 z 2")).toBeVisible();
  await page.getByRole("button", { name: "Dodaj członka", exact: true }).click();
  await expect(page.getByLabel("Relacja rodzinna").locator("option")).toHaveCount(52);
});

test("spóźnione dane rodziny nie wracają po zmianie domu", async ({ page }) => {
  const state = await mockRecords(page, { members: [member("member-a", "Osoba A")] });
  let release!: () => void;
  state.delayHomeAMembers = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.goto("/");
  await expect(page.getByText("Pobieranie danych rodziny…")).toBeVisible();
  await page.getByLabel("Aktywne gospodarstwo").selectOption("home-b");
  await expect(page.getByRole("article", { name: "Osoba B", exact: true })).toBeVisible();
  release();
  await expect(page.getByRole("article", { name: "Osoba A", exact: true })).toHaveCount(0);
  await expect(page.getByLabel("Aktywne gospodarstwo")).toHaveValue("home-b");
});

test("ustawienia pozostają dostępne klawiaturą", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockRecords(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Zarządzanie rodziną", exact: true }).focus();
  await page.keyboard.press("Tab");
  const settings = page.getByRole("button", { name: "Ustawienia", exact: true });
  await expect(settings).toBeFocused();
  expect(await settings.evaluate((element) => getComputedStyle(element).outlineWidth)).toBe("3px");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Dostęp użytkowników" })).toBeVisible();
  const table = page.getByRole("region", { name: /Dostępy użytkowników/ });
  await table.focus();
  await page.keyboard.press("ArrowRight");
  await expect.poll(() => table.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
});
