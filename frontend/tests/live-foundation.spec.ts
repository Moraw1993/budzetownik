import { execFileSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { expect, test } from "@playwright/test";

const liveRun = process.env.LIVE_E2E === "1";
const runId = randomUUID().replaceAll("-", "").slice(0, 12);
const owner = `e2e_owner_${runId}`;
const invited = `e2e_invited_${runId}`;
const household = `Dom testowy ${runId}`;
const password = `E2E-${runId}-Strong-Password!`;
const projectRoot = path.resolve(process.cwd(), "..");

function django(code: string): void {
  execFileSync(
    "docker",
    ["compose", "exec", "-T", "backend", "python", "manage.py", "shell", "-c", code],
    { cwd: projectRoot, stdio: "pipe" },
  );
}

test.describe("rzeczywisty przepływ fundamentu", () => {
  test.skip(!liveRun, "Ustaw LIVE_E2E=1, aby użyć lokalnego API i bazy testowej.");

  test.beforeAll(() => {
    django(
      `from accounts.models import User; User.objects.create_user(username=${JSON.stringify(owner)}, password=${JSON.stringify(password)})`,
    );
  });

  test.afterAll(() => {
    django(
      `from accounts.models import User; from households.models import Household; Household.objects.filter(name=${JSON.stringify(household)}).delete(); User.objects.filter(username__in=[${JSON.stringify(owner)}, ${JSON.stringify(invited)}]).delete()`,
    );
  });

  test("konto, gospodarstwo i zaproszenie działają przez HTTPS", async ({ page }) => {
    await page.goto("/");
    await page.getByLabel("Login", { exact: true }).fill(owner);
    await page.getByLabel("Hasło", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();

    await expect(
      page.getByRole("heading", { name: "Nowe gospodarstwo", exact: true }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Nowe gospodarstwo", exact: true })).toHaveCount(
      0,
    );
    await page.getByLabel("Nazwa gospodarstwa").fill(household);
    await page.getByRole("button", { name: "Utwórz gospodarstwo" }).click();
    await expect(page.getByRole("heading", { name: household, exact: true })).toBeVisible();
    await expect(page.getByText("Owner", { exact: true }).first()).toBeVisible();

    await page.getByRole("button", { name: "Ustawienia" }).click();
    await page.getByLabel("Rola aplikacyjna").selectOption("viewer");
    await page.getByRole("button", { name: "Utwórz zaproszenie" }).click();
    const invitationUrl = await page.getByLabel("Nowy link", { exact: false }).inputValue();
    expect(new URL(invitationUrl).hash.length).toBeGreaterThan(20);

    await page.getByRole("button", { name: "Wyloguj się" }).click();
    await page.goto(invitationUrl);
    await page.getByRole("button", { name: "Nie mam konta", exact: false }).click();
    await page.getByLabel("Login", { exact: true }).fill(invited);
    await page.getByLabel("Hasło", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Utwórz konto i dołącz" }).click();

    await expect(page.getByRole("heading", { name: household, exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Ustawienia" }).click();
    await expect(page.getByText("Tryb odczytu.", { exact: false })).toBeVisible();
    await expect(page.getByRole("button", { name: "Zapisz rolę" })).toHaveCount(0);
    expect(new URL(page.url()).hash).toBe("");
    expect(new URL(page.url()).pathname).toBe("/");

    await page.goto(invitationUrl);
    await page.getByRole("button", { name: "Przyjmij zaproszenie" }).click();
    await expect(page.locator(".notice[role=alert]")).toContainText("Poproś Ownera o nowy link");
  });
});
