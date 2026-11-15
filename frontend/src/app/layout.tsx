import "@fontsource-variable/ibm-plex-sans";
import "@fontsource-variable/bricolage-grotesque";
import "./globals.css";
import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: { default: "Budget Tracker: catch overspending while it's happening", template: "%s · Budget Tracker" },
  description:
    "Set monthly limits, auto-categorise spending and get warned at 80% and 100% of a budget, in real time.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f6f5" },
    { media: "(prefers-color-scheme: dark)", color: "#0e1412" },
  ],
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
