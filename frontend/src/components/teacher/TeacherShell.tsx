import type { ReactNode } from "react";
import { WorkspaceShell } from "@/components/layout/WorkspaceShell";

export function TeacherShell({ children, activePage = "monetization" }: { children: ReactNode; activePage?: "courses" | "doubts" | "monetization" }) {
  return (
    <WorkspaceShell
      footer="Área do professor"
      homeHref="/professor/cursos"
      navigation={[
        { href: "/professor/cursos", icon: "courses", label: "Meus cursos", selected: activePage === "courses" },
        { href: "/professor/duvidas", icon: "doubts", label: "Dúvidas", selected: activePage === "doubts" },
        { href: "/professor/monetizacao", icon: "materials", label: "Monetização", selected: activePage === "monetization" },
      ]}
      role="teacher"
      header={{ type: "title", title: activePage === "courses" ? "Gestão de cursos" : activePage === "doubts" ? "Dúvidas dos alunos" : "Desempenho do professor" }}
    >
      {children}
    </WorkspaceShell>
  );
}
