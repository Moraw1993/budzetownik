import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Domowe Finanse",
  description: "Twoje gospodarstwo. Twój plan.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pl">
      <body>{children}</body>
    </html>
  );
}
