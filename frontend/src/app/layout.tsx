import type { Metadata } from "next";
import { Rubik } from "next/font/google";
import { ApiSessionSync } from "@/components/access/ApiSessionSync";
import { WorkspaceSidebarProvider } from "@/components/layout/WorkspaceSidebarState";
import "./globals.css";

const rubik = Rubik({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "AprovaAí",
  description: "Protótipo inicial da plataforma AprovaAí",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={rubik.className}>
        <WorkspaceSidebarProvider>
          <ApiSessionSync />
          {children}
        </WorkspaceSidebarProvider>
      </body>
    </html>
  );
}
