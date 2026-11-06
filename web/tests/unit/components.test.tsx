import { render, screen } from "@testing-library/react";
import axe from "axe-core";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { BandKey } from "@/components/BandKey";
import { BandSwatch } from "@/components/BandSwatch";
import { Button } from "@/components/Button";
import { ExternalLink } from "@/components/ExternalLink";
import { Notice } from "@/components/Notice";
import { SiteFooter } from "@/components/SiteFooter";
import { StatusBadge } from "@/components/StatusBadge";
import { TextField } from "@/components/TextField";

async function violations(ui: ReactElement) {
  const { container } = render(ui);
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((violation) => violation.id);
}

describe("BandKey", () => {
  it("names every level with its yearly chance, highest first", () => {
    render(<BandKey />);
    const rows = screen.getAllByRole("listitem").map((row) => row.textContent);
    expect(rows).toEqual([
      "High1 in 30 or more",
      "MediumBetween 1 in 30 and 1 in 100",
      "LowBetween 1 in 100 and 1 in 1,000",
      "Very LowBelow 1 in 1,000",
    ]);
  });

  it("gives every level its own pattern", () => {
    const { container } = render(<BandKey />);
    const patterns = [...container.querySelectorAll("[data-pattern]")].map((node) =>
      node.getAttribute("data-pattern"),
    );
    expect(new Set(patterns).size).toBe(4);
  });

  it("hides the pattern from screen readers", () => {
    const { container } = render(<BandSwatch pattern="high" />);
    expect(container.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  it("passes the accessibility checks", async () => {
    expect(await violations(<BandKey />)).toEqual([]);
  });
});

describe("StatusBadge", () => {
  it("shows nothing for an ordinary result", () => {
    const { container } = render(<StatusBadge status="available" />);
    expect(container.textContent).toBe("");
  });

  it.each([
    ["no_data", "No data"],
    ["incomplete", "May be incomplete"],
    ["not_available_here", "Not available here yet"],
  ])("labels %s in words", (status, label) => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText(label)).toBeTruthy();
  });

  it("flags a status it doesn't recognise, so it can't pass as a normal result", () => {
    render(<StatusBadge status="something_new" />);
    expect(screen.getByText("Check this result")).toBeTruthy();
  });

  it("isn't fooled by built-in object names", () => {
    render(<StatusBadge status="constructor" />);
    expect(screen.getByText("Check this result")).toBeTruthy();
  });
});

describe("TextField", () => {
  it("connects the label, hint and error to the box", () => {
    render(
      <TextField label="Postcode" hint="For example, SW1A 1AA" error="Enter a full postcode." />,
    );
    const input = screen.getByLabelText("Postcode");
    expect(input.getAttribute("aria-invalid")).toBe("true");
    const described = input.getAttribute("aria-describedby")?.split(" ") ?? [];
    expect(described.map((id) => document.getElementById(id)?.textContent)).toEqual([
      "For example, SW1A 1AA",
      "Enter a full postcode.",
    ]);
  });

  it("passes the accessibility checks", async () => {
    expect(await violations(<TextField label="Postcode" error="Enter a full postcode." />)).toEqual(
      [],
    );
  });
});

describe("Button", () => {
  it("doesn't submit a form unless asked to", () => {
    render(<Button>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" }).getAttribute("type")).toBe("button");
  });
});

describe("ExternalLink", () => {
  it("opens safely in a new tab and says so", () => {
    render(<ExternalLink href="https://www.gov.uk/">GOV.UK</ExternalLink>);
    const link = screen.getByRole("link", { name: "GOV.UK, opens in a new tab" });
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  });

  it.each(["javascript:alert(1)", "data:text/html,hi", "not a url"])(
    "refuses to link to %s",
    (href) => {
      render(<ExternalLink href={href}>Guidance</ExternalLink>);
      expect(screen.queryByRole("link")).toBeNull();
      expect(screen.getByText("Guidance")).toBeTruthy();
    },
  );
});

describe("Notice", () => {
  it("announces errors straight away", () => {
    render(
      <Notice title="That didn't work" tone="error">
        Try again.
      </Notice>,
    );
    expect(screen.getByRole("alert").textContent).toContain("That didn't work");
  });

  it("doesn't interrupt for ordinary information", () => {
    render(<Notice title="Good to know">Details.</Notice>);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("SiteFooter", () => {
  it("labels each group of information", () => {
    render(<SiteFooter />);
    const headings = screen.getAllByRole("heading").map((heading) => heading.textContent);
    expect(headings).toEqual(["Data sources", "Project", "Your privacy"]);
  });

  it("credits the data's publishers and licence", () => {
    render(<SiteFooter />);
    const footer = screen.getByRole("contentinfo").textContent;
    expect(footer).toContain("© Environment Agency copyright and/or database right 2025");
    expect(footer).toContain("BGS © UKRI");
    expect(footer).toContain("Open Government Licence");
  });

  it("passes the accessibility checks", async () => {
    expect(await violations(<SiteFooter />)).toEqual([]);
  });
});
