import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Logos Academy",
  description: "Protótipo inicial da plataforma Logos Academy",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
