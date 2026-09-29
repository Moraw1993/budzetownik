import { expect, test, type Page } from "@playwright/test";
import type { Household, Invitation, Membership, Role } from "../app/lib/api";

const houses: Household[] = [
  { id: "home-a", name: "Dom rodzinny", currency: "PLN", role: "owner", membership_id: "access-a" },
  {
    id: "home-b",
    name: "Dom rodziców",
    currency: "PLN",
    role: "viewer",
    membership_id: "access-b",
  },
];

async function mockApi(
  page: Page,
  options: { signedIn?: boolean; setup?: boolean; role?: Role } = {},
) {
  const state = {
    signedIn: options.signedIn ?? true,
    setup: options.setup ?? false,
    homes: houses.map((home) => ({ ...home, ...(options.role ? { role: options.role } : {}) })),
    invitations: [] as Invitation[],
    requests: [] as { path: string; method: string; body: Record<string, string> | null }[],
    delayMembers: null as null | Promise<void>,
    delayWrite: null as null | Promise<void>,
    roleDenied: false,
    loginDenied: false,
    serverError: false,
  };
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    const body = request.postDataJSON() as Record<string, string> | null;
    state.requests.push({ path, method, body });
    const reply = (data: unknown, status = 200) => route.fulfill({ status, json: data });
    if (state.serverError)
      return route.fulfill({
        status: 500,
        contentType: "text/html",
        body: "INTERNAL SECRET STACK",
      });
    if (method !== "GET" && request.headers()["x-csrftoken"] !== "fixture-csrf")
      return reply({}, 403);
    if (path === "/api/auth/setup/" && method === "GET")
      return reply({ setup_required: state.setup, csrf_token: "fixture-csrf" });
    if (path === "/api/auth/me/")
      return reply(state.signedIn ? { id: 1, username: "arek" } : {}, state.signedIn ? 200 : 403);
    if (path === "/api/auth/logout/") {
      state.signedIn = false;
      return route.fulfill({ status: 204 });
    }
    if (path === "/api/auth/login/" || path === "/api/auth/setup/") {
      if (state.loginDenied) return reply({ detail: "Nieprawidłowy login lub hasło." }, 401);
      if (state.setup && body?.password === "short")
        return reply({ password: ["Hasło musi mieć co najmniej 12 znaków."] }, 400);
      state.signedIn = true;
      state.setup = false;
      return reply({ id: 1, username: body?.username });
    }
    if (path === "/api/invitations/accept/") {
      if (body?.token !== "valid-fixture-token")
        return reply({ detail: "Zaproszenie jest nieprawidłowe lub niedostępne." }, 400);
      state.signedIn = true;
      return reply({ id: "access-b", user_id: 1, username: "arek", role: "viewer" });
    }
    if (!state.signedIn) return reply({}, 403);
    if (path === "/api/households/") {
      if (method === "POST") {
        if (state.delayWrite) await state.delayWrite;
        const home = {
          ...houses[0],
          id: "home-c",
          name: body?.name ?? "",
          currency: body?.currency ?? "PLN",
          membership_id: "access-c",
        };
        state.homes.push(home);
        return reply(home, 201);
      }
      return reply(state.homes);
    }
    const home = state.homes.find((item) => path.includes("/" + item.id + "/"));
    if (!home) return reply({}, 404);
    if (
      ["/members/", "/relation-types/", "/income-sources/", "/companies/", "/contracts/"].some(
        (suffix) => path.endsWith(suffix),
      )
    )
      return reply({ count: 0, next: null, previous: null, results: [] });
    if (path.endsWith("/memberships/")) {
      if (home.id === "home-a" && state.delayMembers) await state.delayMembers;
      return reply([
        {
          id: home.membership_id,
          user_id: 1,
          username: home.id === "home-a" ? "arek" : "dom-b-użytkownik",
          role: home.role,
        },
      ] satisfies Membership[]);
    }
    if (method === "PATCH") {
      if (state.roleDenied) {
        home.role = "viewer";
        return reply({}, 403);
      }
      if (body?.role !== "owner") return reply({ code: "last_owner" }, 409);
      return reply({});
    }
    if (path.endsWith("/invitations/")) {
      if (home.role !== "owner") return reply({}, 403);
      if (method === "POST") {
        const invitation: Invitation = {
          id: "invite-a",
          role: body?.role as Role,
          expires_at: "2099-09-27T12:00:00Z",
          revoked_at: null,
          accepted_at: null,
        };
        state.invitations.push(invitation);
        return reply(
          {
            ...invitation,
            invitation_url: "http://127.0.0.1:3100/accept-invitation#valid-fixture-token",
          },
          201,
        );
      }
      return reply(state.invitations);
    }
    if (method === "DELETE") {
      state.invitations[0].revoked_at = "2026-09-20T12:00:00Z";
      return route.fulfill({ status: 204 });
    }
    return reply({}, 404);
  });
  return state;
}

test("pierwsze konto: walidacja zachowuje login, usuwa hasło i prowadzi do gospodarstw", async ({
  page,
}) => {
  await mockApi(page, { signedIn: false, setup: true });
  await page.goto("/");
  await page.getByLabel("Login", { exact: true }).fill("nowa-osoba");
  await page.getByLabel("Hasło", { exact: true }).fill("short");
  await page.getByRole("button", { name: "Utwórz konto", exact: true }).click();
  await expect(page.getByText("Hasło musi mieć co najmniej 12 znaków.")).toBeVisible();
  await expect(page.getByLabel("Login", { exact: true })).toHaveValue("nowa-osoba");
  await expect(page.getByLabel("Hasło", { exact: true })).toHaveValue("");
  await expect(page.locator(".notice[role=alert]")).toBeFocused();
  await page.getByLabel("Hasło", { exact: true }).fill("Fixture-Password-123!");
  await page.getByLabel("Hasło", { exact: true }).press("Enter");
  await expect(
    page.getByRole("heading", { name: "Twoja rodzina, w jednym miejscu", exact: true }),
  ).toBeVisible();
});

test("błędne logowanie i wylogowanie z ponowną kontrolą historii", async ({ page }) => {
  const state = await mockApi(page, { signedIn: false });
  state.loginDenied = true;
  await page.goto("/");
  await page.getByLabel("Login", { exact: true }).fill("arek");
  await page.getByLabel("Hasło", { exact: true }).fill("Fixture-Password-123!");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.locator(".notice[role=alert]")).toContainText("Nieprawidłowy login");
  state.loginDenied = false;
  await page.getByLabel("Hasło", { exact: true }).fill("Fixture-Password-123!");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await page.getByRole("button", { name: "Wyloguj się" }).click();
  await expect(page.getByRole("heading", { name: "Zaloguj się", exact: true })).toBeVisible();
  await page.evaluate(() =>
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })),
  );
  await expect(page.getByRole("heading", { name: "Zaloguj się", exact: true })).toBeVisible();
  await expect(page.getByText("Dom rodzinny", { exact: true })).toHaveCount(0);
});

test("spóźniony odczyt nie nadpisuje nowego gospodarstwa", async ({ page }) => {
  const state = await mockApi(page);
  let release!: () => void;
  state.delayMembers = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.goto("/");
  await expect(page.getByText("Pobieranie członków i relacji…")).toBeVisible();
  await page.getByLabel("Aktywne gospodarstwo").selectOption("home-b");
  await page.getByRole("button", { name: "Ustawienia" }).click();
  await expect(page.getByText("dom-b-użytkownik", { exact: true })).toBeVisible();
  release();
  await expect(page.getByRole("heading", { name: "Ustawienia gospodarstwa" })).toBeVisible();
  await expect(page.getByLabel("Aktywne gospodarstwo")).toHaveValue("home-b");
  await expect(page.getByRole("heading", { name: "Zaproszenia", exact: true })).toHaveCount(0);
  await expect(page.getByRole("rowheader", { name: "arek", exact: true })).toHaveCount(0);
});

for (const role of ["administrator", "member", "viewer"] as const) {
  test(role + " ma wyłącznie odczyt ról i nie pobiera zaproszeń", async ({ page }) => {
    const state = await mockApi(page, { role });
    await page.goto("/");
    await page.getByRole("button", { name: "Ustawienia" }).click();
    await expect(page.getByText("Tryb odczytu.", { exact: false })).toBeVisible();
    await expect(page.getByRole("button", { name: "Zapisz rolę" })).toHaveCount(0);
    expect(state.requests.filter((request) => request.path.includes("invitations"))).toHaveLength(
      0,
    );
  });
}

test("ochrona ostatniego Ownera i odświeżenie odebranych uprawnień", async ({ page }) => {
  const state = await mockApi(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Ustawienia" }).click();
  await expect(page.getByLabel("Rola użytkownika arek")).toHaveValue("owner");
  await page.getByLabel("Rola użytkownika arek").selectOption("viewer");
  await page.getByRole("button", { name: "Zapisz rolę" }).click();
  await expect(page.locator(".notice[role=alert]")).toContainText("Ownera");
  state.roleDenied = true;
  await page.getByRole("button", { name: "Zapisz rolę" }).click();
  await expect(page.getByText("Tryb odczytu.", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Zapisz rolę" })).toHaveCount(0);
});

test("utworzenie gospodarstwa wybiera nowy kontekst", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  await page.getByLabel("Aktywne gospodarstwo").selectOption("create");
  await page.getByLabel("Nazwa gospodarstwa").fill("Nowy dom");
  await page.getByRole("button", { name: "Utwórz gospodarstwo" }).click();
  await expect(page.getByLabel("Aktywne gospodarstwo").locator("option:checked")).toHaveText(
    "Nowy dom",
  );
  await expect(page.getByLabel("Aktywne gospodarstwo")).toHaveValue("home-c");
});

test("wystawienie i odwołanie zaproszenia, fallback kopiowania", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Ustawienia" }).click();
  await page.getByRole("button", { name: "Utwórz zaproszenie" }).click();
  await expect(page.getByLabel("Nowy link", { exact: false })).toHaveValue(/#valid-fixture-token$/);
  await page.evaluate(() => {
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: () => Promise.reject(new Error("denied")) },
    });
  });
  await page.getByRole("button", { name: "Kopiuj link" }).click();
  await expect(page.getByRole("status")).toContainText("ręcznie");
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.getByRole("button", { name: "Odwołaj zaproszenie" }).click();
  await expect(page.getByText("○ Aktywne")).toBeVisible();
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Odwołaj zaproszenie" }).click();
  await expect(page.getByText("○ Odwołane")).toBeVisible();
  await expect(page.getByLabel("Nowy link", { exact: false })).toHaveCount(0);
});

test("zaproszona osoba tworzy konto, token znika z adresu i wybiera właściwy dom", async ({
  page,
}) => {
  const state = await mockApi(page, { signedIn: false });
  await page.goto("/accept-invitation#valid-fixture-token");
  await page.getByRole("button", { name: "Nie mam konta", exact: false }).click();
  await page.getByLabel("Login", { exact: true }).fill("nowa-osoba");
  await page.getByLabel("Hasło", { exact: true }).fill("Fixture-Password-123!");
  await page.getByRole("button", { name: "Utwórz konto i dołącz" }).click();
  await expect(page.getByLabel("Aktywne gospodarstwo").locator("option:checked")).toHaveText(
    "Dom rodziców",
  );
  expect(new URL(page.url()).hash).toBe("");
  expect(new URL(page.url()).pathname).toBe("/");
  expect(
    state.requests.find((request) => request.path === "/api/invitations/accept/")?.body?.token,
  ).toBe("valid-fixture-token");
});

test("zaproszenie zachowuje token podczas logowania istniejącej osoby", async ({ page }) => {
  await mockApi(page, { signedIn: false });
  await page.goto("/accept-invitation#valid-fixture-token");
  await page.getByLabel("Login", { exact: true }).fill("arek");
  await page.getByLabel("Hasło", { exact: true }).fill("Fixture-Password-123!");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await page.getByRole("button", { name: "Przyjmij zaproszenie" }).click();
  await expect(page.getByLabel("Aktywne gospodarstwo").locator("option:checked")).toHaveText(
    "Dom rodziców",
  );
});

test("zużyty lub nieprawidłowy link pokazuje czytelny błąd", async ({ page }) => {
  await mockApi(page);
  await page.goto("/accept-invitation#invalid-fixture-token");
  await page.getByRole("button", { name: "Przyjmij zaproszenie" }).click();
  await expect(page.locator(".notice[role=alert]")).toContainText("Poproś Ownera o nowy link");
});

test("błąd serwera nie ujawnia jego treści, ponowienie przywraca widok", async ({ page }) => {
  const state = await mockApi(page);
  state.serverError = true;
  await page.goto("/");
  await expect(page.locator(".notice[role=alert]")).toContainText(
    "Serwer jest chwilowo niedostępny",
  );
  await expect(page.getByText("INTERNAL SECRET STACK")).toHaveCount(0);
  state.serverError = false;
  await page.getByRole("button", { name: "Spróbuj ponownie" }).click();
  await expect(
    page.getByRole("heading", { name: "Twoja rodzina, w jednym miejscu", exact: true }),
  ).toBeVisible();
});

test("desktop i telefon zachowują akcje bez przewijania całej strony w poziomie", async ({
  page,
}) => {
  await mockApi(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await page.getByRole("button", { name: "Ustawienia" }).click();
  await expect(page.getByRole("button", { name: "Utwórz zaproszenie" })).toBeVisible();
  await page.screenshot({ path: "../.runtime/bolt006-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("button", { name: "Wyloguj się" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  const table = page.getByRole("region", { name: "Dostępy użytkowników", exact: false });
  await table.focus();
  await expect(table).toBeFocused();
  await page.keyboard.press("ArrowRight");
  await expect.poll(() => table.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
  await table.evaluate((element) => {
    element.scrollLeft = 0;
  });
  await page.screenshot({ path: "../.runtime/bolt006-mobile.png", fullPage: true });
});

test("ukończenie starego zapisu nie zmienia nowo wybranego gospodarstwa", async ({ page }) => {
  const state = await mockApi(page);
  let release!: () => void;
  state.delayWrite = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.goto("/");
  await page.getByLabel("Aktywne gospodarstwo").selectOption("create");
  await page.getByLabel("Nazwa gospodarstwa").fill("Opóźniony dom");
  await page.getByRole("button", { name: "Utwórz gospodarstwo" }).click();
  await expect
    .poll(() =>
      state.requests.some(
        (request) => request.path === "/api/households/" && request.method === "POST",
      ),
    )
    .toBe(true);
  await page.getByRole("button", { name: "Anuluj", exact: true }).click();
  await page.getByLabel("Aktywne gospodarstwo").selectOption("home-b");
  const completed = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/households/") && response.request().method() === "POST",
  );
  release();
  await completed;
  await page.getByRole("button", { name: "Ustawienia" }).click();
  await expect(page.getByText("dom-b-użytkownik", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Aktywne gospodarstwo")).toHaveValue("home-b");
});

test("powrót do strony zachowuje wybrane gospodarstwo, wygaśnięcie sesji usuwa dane", async ({
  page,
}) => {
  const state = await mockApi(page);
  await page.goto("/");
  await page.getByLabel("Aktywne gospodarstwo").selectOption("home-b");
  await page.evaluate(() =>
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })),
  );
  await expect(page.getByLabel("Aktywne gospodarstwo")).toHaveValue("home-b");
  state.signedIn = false;
  await page.evaluate(() =>
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })),
  );
  await expect(page.getByRole("heading", { name: "Zaloguj się", exact: true })).toBeVisible();
  await expect(page.getByText("Dom rodziców", { exact: true })).toHaveCount(0);
});

test("nieudane wylogowanie nie udaje zakończonej sesji", async ({ page }) => {
  const state = await mockApi(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Ustawienia" }).click();
  await expect(page.getByRole("button", { name: "Utwórz zaproszenie" })).toBeVisible();
  state.serverError = true;
  await page.getByRole("button", { name: "Wyloguj się" }).click();
  await expect(page.locator(".notice[role=alert]")).toContainText(
    "Serwer jest chwilowo niedostępny",
  );
  await expect(page.getByRole("heading", { name: "Ustawienia gospodarstwa" })).toBeVisible();
});

test("dostępy są w ustawieniach aktywnego gospodarstwa", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockApi(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Członkowie rodziny" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dostęp użytkowników" })).toHaveCount(0);
  await page.getByRole("button", { name: "Ustawienia" }).click();
  await expect(page.getByRole("heading", { name: "Ustawienia gospodarstwa" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dostęp użytkowników" })).toBeVisible();
  await expect(page.locator(".topbar")).toContainText(
    "Gospodarstwa / Dom rodzinny / Ustawienia gospodarstwa / Dostępy",
  );
  const roleAction = await page.getByRole("button", { name: "Zapisz rolę" }).boundingBox();
  expect(roleAction!.width).toBeLessThan(200);
  await page.screenshot({
    path: "../.runtime/bolt011-settings-1440.png",
    fullPage: true,
  });
  await page.getByLabel("Aktywne gospodarstwo").selectOption("home-b");
  await expect(page.getByRole("heading", { name: "Członkowie rodziny" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dostęp użytkowników" })).toHaveCount(0);
});
