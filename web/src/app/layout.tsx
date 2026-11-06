import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "@fontsource-variable/atkinson-hyperlegible-next";
import "@/styles/tokens.css";
import "@/styles/base.css";
import { SkipLink } from "@/components/SkipLink";
import { SiteFooter } from "@/components/SiteFooter";

export const metadata: Metadata = {
  title: "PerilMap: climate risks around a home",
  description:
    "See the flood, heat and ground movement information for the area around a home in London, before the insurance quote arrives.",
};

export const viewport: Viewport = {
  themeColor: "#2f1218",
};

// Each page view gets its own script code from src/proxy.ts, so pages can't be saved ahead of time.
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en-GB">
      <body>
        <SkipLink />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
