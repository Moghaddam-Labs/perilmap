import { describe, expect, it } from "vitest";
import { bandDisplay } from "@/lib/bands";
import { apiOrigin, isDesignPageEnabled, LIVE_API_URL } from "@/lib/config";
import { contentSecurityPolicy, staticSecurityHeaders } from "@/lib/security";

describe("apiOrigin", () => {
  it("uses the live API by default", () => {
    expect(apiOrigin("")).toBe(LIVE_API_URL);
  });

  it("allows plain http only on this computer", () => {
    expect(apiOrigin("http://127.0.0.1:8000")).toBe("http://127.0.0.1:8000");
    expect(() => apiOrigin("http://example.com")).toThrow(/https/);
  });

  it("rejects a value that isn't a web address", () => {
    expect(() => apiOrigin("nope")).toThrow(/valid/);
  });

  it("keeps only the origin, so a stray path can't widen or break the policy", () => {
    expect(apiOrigin("https://api.example.com/v1; script-src *")).toBe("https://api.example.com");
  });
});

describe("isDesignPageEnabled", () => {
  it("is hidden on a production build unless asked for", () => {
    expect(isDesignPageEnabled({ NODE_ENV: "production" })).toBe(false);
    expect(isDesignPageEnabled({ NODE_ENV: "production", PERILMAP_SHOW_DESIGN_PAGE: "true" })).toBe(
      true,
    );
    expect(isDesignPageEnabled({ NODE_ENV: "development" })).toBe(true);
  });
});

describe("bandDisplay", () => {
  it("keeps the source's name for a band it doesn't know, without implying a level", () => {
    expect(bandDisplay("Severe")).toEqual({ label: "Severe", pattern: "other" });
    expect(bandDisplay("toString").pattern).toBe("other");
  });
});

describe("contentSecurityPolicy", () => {
  const policy = contentSecurityPolicy({ nonce: "abc", apiOrigin: "https://api.example.com" });

  it("only lets the site's own scripts run", () => {
    expect(policy).toContain("script-src 'self' 'nonce-abc' 'strict-dynamic'");
    expect(policy).not.toContain("unsafe-inline");
    expect(policy).not.toContain("unsafe-eval");
  });

  it("only lets data go to the site and its API", () => {
    expect(policy).toContain("connect-src 'self' https://api.example.com");
    expect(policy).toContain("form-action 'self'");
  });

  it("can't be framed by another site", () => {
    expect(policy).toContain("frame-ancestors 'none'");
  });

  it("never sends the page address to other sites", () => {
    expect(staticSecurityHeaders).toContainEqual({ key: "Referrer-Policy", value: "no-referrer" });
  });
});
