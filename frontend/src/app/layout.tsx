import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { ResourceProvider } from "@/context/ResourceContext";

export const metadata: Metadata = {
  title: "SmartSched AI | University Timetable Operations",
  description: "Enterprise Academic Timetable Generation using Constraint-Based Search (CSP) and Genetic Algorithms.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <ResourceProvider>
          <AppShell>{children}</AppShell>
        </ResourceProvider>
      </body>
    </html>
  );
}
