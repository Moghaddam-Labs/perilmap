import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PostcodeSearch } from "@/components/PostcodeSearch";

function stubLookup(status: number, body: unknown) {
  const fetchMock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function search(text: string) {
  const onFound = vi.fn();
  render(<PostcodeSearch onFound={onFound} />);
  const box = screen.getByLabelText("Postcode");
  if (text) await userEvent.type(box, text);
  await userEvent.click(screen.getByRole("button", { name: "Find postcode" }));
  return { onFound, box };
}

afterEach(() => vi.unstubAllGlobals());

describe("PostcodeSearch", () => {
  it("asks for a postcode when the box is empty, without sending anything", async () => {
    const fetchMock = stubLookup(200, {});
    const { box } = await search("");
    expect(await screen.findByText("Enter a postcode.")).toBeTruthy();
    expect(box).toHaveProperty("ariaInvalid", "true");
    expect(document.activeElement).toBe(box);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("catches text that isn't a postcode before sending it", async () => {
    const fetchMock = stubLookup(200, {});
    await search("not a postcode");
    expect(await screen.findByText("Enter a full UK postcode, such as SW1A 2AA.")).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("passes on a London postcode's position", async () => {
    stubLookup(200, {
      postcode: "SW1A 2AA",
      latitude: 51.5035,
      longitude: -0.1276,
      attribution: "Postcode lookup by postcodes.io",
    });
    const { onFound, box } = await search("sw1a2aa");
    await vi.waitFor(() => expect(onFound).toHaveBeenCalled());
    expect(onFound).toHaveBeenCalledWith({
      postcode: "SW1A 2AA",
      latitude: 51.5035,
      longitude: -0.1276,
    });
    expect((box as HTMLInputElement).value).toBe("SW1A 2AA");
  });

  it("explains when a postcode is outside London", async () => {
    stubLookup(200, {
      postcode: "RG1 1AA",
      latitude: 51.4543,
      longitude: -0.9781,
      attribution: "Postcode lookup by postcodes.io",
    });
    const { onFound } = await search("RG1 1AA");
    expect(await screen.findByText(/RG1 1AA is outside Greater London/)).toBeTruthy();
    expect(onFound).not.toHaveBeenCalled();
  });

  it("says when the postcode doesn't exist", async () => {
    stubLookup(404, { detail: "We couldn't find that postcode." });
    await search("ZZ9 9ZZ");
    expect(await screen.findByText(/We couldn't find that postcode/)).toBeTruthy();
  });
});
