import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, request, setApiKey } from "./api";

function mockFetch(response) {
  const fn = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fn);
  return fn;
}
const json = (body, init = {}) => new Response(JSON.stringify(body), { headers: { "Content-Type": "application/json" }, ...init });

afterEach(() => {
  vi.unstubAllGlobals();
  setApiKey("");
});

describe("api client", () => {
  it("sends the API key and query params, skipping empty ones", async () => {
    setApiKey("secret");
    const fetchMock = mockFetch(json([{ asin: "B012345678" }], { headers: { "Content-Type": "application/json", "X-Total-Count": "42" } }));
    const result = await request("/asins", { params: { q: "6205", limit: 20, offset: "" } });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/asins?q=6205&limit=20");
    expect(init.headers["X-API-Key"]).toBe("secret");
    expect(result.total).toBe(42);
  });

  it("turns FastAPI validation arrays into readable messages", async () => {
    mockFetch(json({ detail: [{ loc: ["body", "asin"], msg: "asin must be 10-char alphanumeric" }] }, { status: 422 }));
    await expect(api.post("/asins", { asin: "x" })).rejects.toMatchObject({ status: 422, message: "asin: asin must be 10-char alphanumeric" });
  });

  it("reports an unreachable backend", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));
    const error = await api.get("/asins").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(0);
  });

  it("returns null for 204 responses", async () => {
    mockFetch(new Response(null, { status: 204 }));
    expect(await api.delete("/asins/B012345678")).toBeNull();
  });
});
