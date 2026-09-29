import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

const runId = process.env.ACCEPTANCE_RUN_ID;

test("dwa gospodarstwa pokazują oddzielnych członków i źródła", async ({ page }) => {
  test.skip(!runId, "Ustaw ACCEPTANCE_RUN_ID dla izolowanej instalacji odbiorowej.");
  if (!runId || !/^[0-9a-f]{8}$/.test(runId)) {
    throw new Error("Nieprawidłowy identyfikator odbioru.");
  }

  const runDir = path.resolve(process.cwd(), "..", ".runtime", "acceptance", runId);
  const manifest = JSON.parse(readFileSync(path.join(runDir, "manifest.json"), "utf8"));
  const fixture = JSON.parse(readFileSync(path.join(runDir, "fixture.json"), "utf8"));
  const [first, second] = fixture.households as string[];
  const baseUrl = `https://localhost:${manifest.source.port}`;

  await page.goto(baseUrl);
  await page.getByLabel("Login", { exact: true }).fill(fixture.owner);
  await page.getByLabel("Hasło").fill(manifest.user_password);
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();

  await page.getByLabel("Aktywne gospodarstwo").selectOption(first);
  await page.getByRole("button", { name: "Członkowie" }).click();
  await expect(page.getByText(`Osoba ${runId}`, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Dochody" }).click();
  await expect(
    page.getByRole("rowheader", { name: new RegExp(`^Dochód osoby 0 ${runId}`) }),
  ).toBeVisible();

  await page.getByLabel("Aktywne gospodarstwo").selectOption(second);
  await page.getByRole("button", { name: "Członkowie" }).click();
  await expect(page.getByText(`Obca osoba ${runId}`, { exact: true })).toBeVisible();
  await expect(page.getByText(`Osoba ${runId}`, { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Dochody" }).click();
  await expect(
    page.getByRole("rowheader", { name: new RegExp(`^Obcy dochód ${runId}`) }),
  ).toBeVisible();
  await expect(
    page.getByRole("rowheader", { name: new RegExp(`^Dochód osoby 0 ${runId}`) }),
  ).toHaveCount(0);
});
