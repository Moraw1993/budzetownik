import { expect, test } from "@playwright/test";
import { api, apiBlob, ApiError } from "../app/lib/api";
import { validateFiles, type Attachment } from "../app/lib/periods-api";

test("multipart keeps browser boundary, fresh CSRF and idempotency headers", async () => {
  const original = globalThis.fetch;
  const calls: { path: string; init?: RequestInit }[] = [];
  globalThis.fetch = async (input, init) => {
    calls.push({ path: String(input), init });
    return new Response(
      JSON.stringify(calls.length === 1 ? { csrf_token: "fresh-token" } : { results: [] }),
      { status: calls.length === 1 ? 200 : 201 },
    );
  };
  try {
    const data = new FormData();
    data.append("files", new File(["png"], "a.png"));
    await api("/files/", {
      method: "POST",
      data,
      headers: { "Idempotency-Key": "attempt" },
      expectedStatus: 201,
    });
    expect(calls[0].path).toBe("/api/auth/setup/");
    const headers = calls[1].init?.headers as Record<string, string>;
    expect(headers["X-CSRFToken"]).toBe("fresh-token");
    expect(headers["Idempotency-Key"]).toBe("attempt");
    expect(headers["Content-Type"]).toBeUndefined();
    expect(calls[1].init?.body).toBe(data);
    expect(calls[1].init?.credentials).toBe("same-origin");
  } finally {
    globalThis.fetch = original;
  }
});
test("unconfirmed response remains unknown and binary errors do not create a blob", async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => new Response("{}", { status: 200 });
    await expect(api("/files/", { expectedStatus: 201 })).rejects.toMatchObject({ status: 0 });
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ detail: "Brak dostępu." }), { status: 403 });
    await expect(apiBlob("/private/")).rejects.toBeInstanceOf(ApiError);
    globalThis.fetch = async () => new Response("broken", { status: 201 });
    await expect(api("/income/")).rejects.toMatchObject({ status: 0 });
  } finally {
    globalThis.fetch = original;
  }
});
test("attachment batch and capacity checks preserve binary limits", () => {
  expect(validateFiles([new File(["x"], "a.pdf")])).toBe("");
  expect(validateFiles([new File(["x"], "a.exe")])).toContain("Dozwolone");
  expect(validateFiles(Array.from({ length: 6 }, () => new File(["x"], "a.png")))).toContain(
    "1 do 5",
  );
  expect(validateFiles([new File([new Uint8Array(10 * 1024 ** 2 + 1)], "a.png")])).toContain(
    "10 MiB",
  );
  const saved = Array.from(
    { length: 20 },
    (_, index) => ({ id: String(index), size_bytes: 1 }) as Attachment,
  );
  expect(validateFiles([new File(["x"], "a.pdf")], saved)).toContain("20 plików");
});
