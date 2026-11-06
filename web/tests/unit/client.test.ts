import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, lookupPostcode } from "@/lib/api/client";
import { LIVE_API_URL } from "@/lib/config";

const FOUND = {
  postcode: "SW1A 2AA",
  latitude: 51.5035,
  longitude: -0.1276,
  attribution: "Postcode lookup by postcodes.io",
};

function respond(status: number, body: unknown = {}) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => vi.unstubAllGlobals());

describe("lookupPostcode", () => {
  it("sends the postcode in the body, never in the web address", async () => {
    const fetchMock = respond(200, FOUND);
    await expect(lookupPostcode("SW1A 2AA")).resolves.toEqual(FOUND);
    const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${LIVE_API_URL}/v1/postcodes/lookup`);
    expect(url).not.toContain("SW1A");
    expect(options.method).toBe("POST");
    expect(options.body).toBe(JSON.stringify({ postcode: "SW1A 2AA" }));
    expect(options.credentials).toBe("omit");
    expect(options.referrerPolicy).toBe("no-referrer");
  });

  it.each([
    [404, "not_found"],
    [422, "invalid"],
    [429, "busy"],
    [503, "unavailable"],
  ])("turns a %d answer into %s", async (status, problem) => {
    respond(status);
    await expect(lookupPostcode("SW1A 2AA")).rejects.toMatchObject({ problem });
  });

  it("treats a dropped connection as unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => Promise.reject(new TypeError("Failed to fetch"))),
    );
    await expect(lookupPostcode("SW1A 2AA")).rejects.toBeInstanceOf(ApiError);
  });

  it("refuses an answer that isn't shaped like a postcode result", async () => {
    respond(200, { postcode: "SW1A 2AA", latitude: "nope" });
    await expect(lookupPostcode("SW1A 2AA")).rejects.toMatchObject({ problem: "unavailable" });
  });
});
