import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, type Page } from "@playwright/test";

type FamilyFixture = {
  users: Record<string, string>;
  households: string[];
  members: string[];
  salary: string;
  foreign_source: string;
};
export function familyFixture(runId = process.env.FAMILY_ACCEPTANCE_RUN_ID) {
  if (!runId || !/^[0-9a-f]{8}$/.test(runId)) throw new Error("Invalid family acceptance run");
  const directory = path.resolve(process.cwd(), "..", ".runtime", "acceptance", runId);
  const manifest = JSON.parse(readFileSync(path.join(directory, "manifest.json"), "utf8"));
  if (manifest.source.project !== `myhomebudget-acceptance-${runId}-source`)
    throw new Error("Unexpected acceptance project");
  const data = JSON.parse(
    readFileSync(path.join(directory, "family-fixture.json"), "utf8"),
  ) as FamilyFixture;
  return {
    directory,
    data,
    password: manifest.user_password as string,
    url: `https://localhost:${manifest.source.port}`,
  };
}
export async function loginFamily(page: Page, role: string) {
  const { data, password, url } = familyFixture();
  await page.goto(url);
  await page.getByLabel("Login", { exact: true }).fill(data.users[role]);
  await page.getByLabel("Hasło", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await page.getByLabel("Aktywne gospodarstwo").selectOption(data.households[0]);
  await expect(page.getByRole("tab", { name: "Członkowie" })).toBeVisible();
  return data;
}
