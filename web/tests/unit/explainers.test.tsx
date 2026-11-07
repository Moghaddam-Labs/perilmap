import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { describe, expect, it } from "vitest";
import { ReadingTheResults } from "@/components/ReadingTheResults";

const card = (name: RegExp) => screen.getByRole("button", { name });
const PANEL_NAMES = /Flood levels|A gap never looks safe|Where the data comes from/;
const openPanels = () => screen.queryAllByRole("region", { name: PANEL_NAMES });

describe("Reading the results cards", () => {
  it("starts with every card closed", () => {
    render(<ReadingTheResults />);
    for (const button of screen.getAllByRole("button")) {
      expect(button.getAttribute("aria-expanded")).toBe("false");
    }
    expect(openPanels()).toHaveLength(0);
  });

  it("opens a card on click, showing all of its information", async () => {
    render(<ReadingTheResults />);
    await userEvent.click(card(/Flood levels/));
    expect(card(/Flood levels/).getAttribute("aria-expanded")).toBe("true");
    const panel = screen.getByRole("region", { name: "Flood levels you can tell apart" });
    for (const text of ["High", "Medium", "Low", "Very Low", "Below 1 in 1,000"]) {
      expect(panel.textContent).toContain(text);
    }
  });

  it("keeps only one card open at a time", async () => {
    render(<ReadingTheResults />);
    await userEvent.click(card(/Flood levels/));
    await userEvent.click(card(/A gap never looks safe/));
    expect(card(/Flood levels/).getAttribute("aria-expanded")).toBe("false");
    expect(openPanels()).toHaveLength(1);
  });

  it("closes when you click somewhere else", async () => {
    render(
      <>
        <ReadingTheResults />
        <p>Elsewhere</p>
      </>,
    );
    await userEvent.click(card(/Where the data comes from/));
    await userEvent.click(screen.getByText("Elsewhere"));
    expect(openPanels()).toHaveLength(0);
  });

  it("closes with Escape and puts focus back on the card", async () => {
    render(<ReadingTheResults />);
    await userEvent.click(card(/A gap never looks safe/));
    await userEvent.keyboard("{Escape}");
    expect(openPanels()).toHaveLength(0);
    expect(document.activeElement).toBe(card(/A gap never looks safe/));
  });

  it("opens with the keyboard", async () => {
    render(<ReadingTheResults />);
    card(/Where the data comes from/).focus();
    await userEvent.keyboard("{Enter}");
    expect(openPanels()[0]?.textContent).toContain("6 July 2026");
  });

  it("names each card by its title and short line, not the show more hint", () => {
    render(<ReadingTheResults />);
    expect(card(/Flood levels/).textContent).toContain("Show more");
    expect(
      screen.getByRole("button", {
        name: "Flood levels you can tell apart The Environment Agency's four levels, each with its own pattern.",
      }),
    ).toBeTruthy();
  });

  it("passes the accessibility checks, open and closed", async () => {
    const { container } = render(<ReadingTheResults />);
    const check = async () =>
      (await axe.run(container, { rules: { "color-contrast": { enabled: false } } })).violations;
    expect(await check()).toEqual([]);
    await userEvent.click(card(/A gap never looks safe/));
    expect(await check()).toEqual([]);
  });
});
