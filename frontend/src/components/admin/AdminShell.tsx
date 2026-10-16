import type { ReactNode } from "react";
import { WorkspaceShell } from "@/components/layout/WorkspaceShell";

type AdminPage = "overview" | "moderation";

export function AdminShell({
  activePage,
  children,
  topbarTitle,
}: {
  activePage: AdminPage;
  children: ReactNode;
  topbarTitle: string;
}) {
  return (
    <WorkspaceShell
      footer="Ambiente administrativo"
      homeHref="/admin"
      navigation={[
        { href: "/admin", icon: "home", label: "Visão geral", selected: activePage === "overview" },
        { href: "/admin/moderacao", icon: "help", label: "Moderação", selected: activePage === "moderation" },
      ]}
      role="admin"
      header={{ type: "title", title: topbarTitle }}
    >
      {children}
    </WorkspaceShell>
  );
}
