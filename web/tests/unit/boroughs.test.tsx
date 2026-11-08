import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BoroughFloodSection } from "@/components/BoroughFloodSection";
import data from "@/lib/borough-flood.json";

describe("BoroughFloodSection", () => {
  it("gives every borough's figures in a table, as well as the chart", () => {
    render(<BoroughFloodSection />);
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(34);
    expect(within(table).getByRole("rowheader", { name: "Southwark" })).toBeTruthy();
  });

  it("draws every borough, stacked by level, highest first", () => {
    const { container } = render(<BoroughFloodSection />);
    const charts = [...container.querySelectorAll("bezel-bars")];
    expect(charts).toHaveLength(2);
    for (const chart of charts) {
      const labels = chart.getAttribute("labels")?.split(",") ?? [];
      expect(labels).toHaveLength(33);
      expect(labels[0]).toBe(data.boroughs[0]?.name);
      expect(chart.hasAttribute("stacked")).toBe(true);
      expect(chart.getAttribute("series")).toBe("Low or higher,Very Low");
      expect(chart.getAttribute("values")?.split("|")).toHaveLength(2);
    }
  });

  it("uses vertical bars with slanted names on wide screens, and horizontal bars on phones", () => {
    const { container } = render(<BoroughFloodSection />);
    const [wide, narrow] = [...container.querySelectorAll("bezel-bars")];
    expect(wide?.hasAttribute("angle-labels")).toBe(true);
    expect(wide?.hasAttribute("horizontal")).toBe(false);
    expect(narrow?.hasAttribute("horizontal")).toBe(true);
  });

  it("explains, from the data, why a small share doesn't mean no risk", () => {
    render(<BoroughFloodSection />);
    expect(
      screen.getByText(/A small blue share doesn't mean no risk\. Southwark has 0\.1%/),
    ).toBeTruthy();
  });

  it("says it's PerilMap's own calculation, and that it covers rivers and the sea only", () => {
    render(<BoroughFloodSection />);
    expect(screen.getByText(/PerilMap's own calculation/)).toBeTruthy();
    expect(screen.getByText(/This covers rivers and the sea only/)).toBeTruthy();
  });
});
