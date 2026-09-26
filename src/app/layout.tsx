import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AprovaAí",
  description: "Protótipo inicial da plataforma AprovaAí",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
