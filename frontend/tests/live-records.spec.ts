import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { expect, test } from "@playwright/test";

const liveRun = process.env.LIVE_E2E === "1";
const runId = randomUUID().replaceAll("-", "").slice(0, 12);
const owner = `e2e_records_owner_${runId}`;
const viewer = `e2e_records_viewer_${runId}`;
const household = `Dom danych ${runId}`;
const member = `Osoba ${runId}`;
const income = `Dochód ${runId}`;
const password = `E2E-${runId}-Strong-Password!`;
const projectRoot = path.resolve(process.cwd(), "..");

function django(code: string): void {
  execFileSync(
    "docker",
    ["compose", "exec", "-T", "backend", "python", "manage.py", "shell", "-c", code],
    { cwd: projectRoot, stdio: "pipe" },
  );
}

test.describe("rzeczywisty przepływ członków i dochodów", () => {
  test.skip(!liveRun, "Ustaw LIVE_E2E=1, aby użyć lokalnego API i bazy testowej.");

  test.beforeAll(() => {
    django(
      `from accounts.models import User; User.objects.create_user(username=${JSON.stringify(owner)}, password=${JSON.stringify(password)}); User.objects.create_user(username=${JSON.stringify(viewer)}, password=${JSON.stringify(password)})`,
    );
  });

  test.afterAll(() => {
    django(
      `from accounts.models import User; from households.models import AuditLog, Household, HouseholdMember, IncomeSource, RelationType; h=Household.objects.filter(name=${JSON.stringify(household)}).first(); AuditLog.objects.filter(household=h).delete() if h else None; IncomeSource.objects.filter(household=h).delete() if h else None; HouseholdMember.objects.filter(household=h).delete() if h else None; RelationType.objects.filter(household=h).delete() if h else None; h.delete() if h else None; User.objects.filter(username__in=[${JSON.stringify(owner)}, ${JSON.stringify(viewer)}]).delete()`,
    );
  });

  test("Owner zapisuje dane, Viewer je odczytuje, a dezaktywacja zachowuje audyt", async ({
    page,
  }) => {
    test.setTimeout(90000);
    await page.goto("/");
    await page.getByLabel("Login", { exact: true }).fill(owner);
    await page.getByLabel("Hasło", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
    await page.getByLabel("Nazwa gospodarstwa").fill(household);
    await page.getByRole("button", { name: "Utwórz gospodarstwo" }).click();
    await expect(page.getByRole("heading", { name: household, exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Członkowie" }).click();
    await page.getByLabel("Nazwa relacji").fill("Rodzic");
    await page.getByRole("button", { name: "Dodaj relację" }).click();
    await expect(page.locator(".record-list").getByText("Rodzic", { exact: true })).toBeVisible();
    await page.getByLabel("Nazwa członka").fill(member);
    await page.getByLabel("Relacja rodzinna").selectOption({ label: "Rodzic" });
    await page.getByLabel("Powiązane konto").selectOption({ label: owner });
    const memberResponse = page.waitForResponse(
      (response) => response.url().endsWith("/members/") && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Dodaj członka" }).click();
    const createdMember = await memberResponse;
    expect(createdMember.status(), await createdMember.text()).toBe(201);
    await expect(page.getByRole("row", { name: new RegExp(member) })).toContainText(owner);

    await page.getByRole("button", { name: "Dochody" }).click();
    await page.getByLabel("Przypisanie dochodu").selectOption({ label: member });
    await page.getByLabel("Nazwa źródła").fill(income);
    await page.getByLabel("Kategoria").fill("praca");
    await page.getByLabel("Płatnik").fill("Firma testowa");
    await page.getByLabel("Częstotliwość").selectOption("monthly");
    await page.getByLabel("Data rozpoczęcia").fill("2026-01-01");
    await page.getByLabel("Domyślna kwota miesięczna").fill("9999999999999999,99");
    await page.getByLabel("Waluta").fill("pln");
    await page.getByLabel("Opis").fill("Test rzeczywistego stosu");
    await page.getByRole("button", { name: "Dodaj źródło" }).click();
    await expect(page.getByRole("row", { name: new RegExp(income) })).toContainText(
      "9 999 999 999 999 999,99 PLN",
    );

    django(
      `from accounts.models import User; from households.models import Household, Membership, Role; Membership.objects.create(household=Household.objects.get(name=${JSON.stringify(household)}), user=User.objects.get(username=${JSON.stringify(viewer)}), role=Role.VIEWER)`,
    );
    await page.getByRole("button", { name: "Wyloguj się" }).click();
    await page.getByLabel("Login", { exact: true }).fill(viewer);
    await page.getByLabel("Hasło", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
    await page.getByRole("button", { name: "Członkowie" }).click();
    await expect(page.getByText(member, { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dodaj|Edytuj|Dezaktywuj/ })).toHaveCount(0);
    await page.getByRole("button", { name: "Dochody" }).click();
    await expect(page.getByRole("row", { name: new RegExp(income) })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dodaj|Edytuj|Dezaktywuj/ })).toHaveCount(0);

    await page.getByRole("button", { name: "Wyloguj się" }).click();
    await page.getByLabel("Login", { exact: true }).fill(owner);
    await page.getByLabel("Hasło", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
    await page.getByRole("button", { name: "Dochody" }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("row", { name: new RegExp(income) })
      .getByRole("button", { name: "Dezaktywuj" })
      .click();
    await expect(page.getByRole("row", { name: new RegExp(income) })).toContainText("Archiwalne");

    django(
      `from decimal import Decimal; from households.models import AuditLog, Household, IncomeSource; h=Household.objects.get(name=${JSON.stringify(household)}); s=IncomeSource.objects.get(household=h, name=${JSON.stringify(income)}); assert s.default_monthly_amount == Decimal('9999999999999999.99'); assert not s.is_active; assert list(AuditLog.objects.filter(household=h, object_id=s.id).order_by('occurred_at').values_list('action', flat=True)) == ['created', 'deactivated']`,
    );
  });
});
