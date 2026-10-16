import type { ReactNode } from "react";
import type { NavIconName } from "./NavIcon";
import { WorkspaceShell } from "./WorkspaceShell";

type StudentPage = "home" | "courses" | "doubts" | "explore" | "materials" | "certificates" | "profile";

const navigation: { label: string; href: string; page: StudentPage; icon: NavIconName }[] = [
  { label: "Início", href: "/", page: "home", icon: "home" },
  { label: "Meus cursos", href: "/meus-cursos", page: "courses", icon: "courses" },
  { label: "Dúvidas", href: "/duvidas", page: "doubts", icon: "doubts" },
  { label: "Explorar", href: "/explorar-cursos", page: "explore", icon: "explore" },
  { label: "Materiais", href: "/materiais-complementares", page: "materials", icon: "materials" },
  { label: "Certificados", href: "/certificados", page: "certificates", icon: "certificates" },
  { label: "Meu perfil", href: "/perfil", page: "profile", icon: "profile" },
];

export function AppShell({ children, activePage }: { children: ReactNode; activePage?: StudentPage }) {
  return (
    <WorkspaceShell
      contentWidth="wide"
      footer="Protótipo inicial"
      header={{ type: "search" }}
      homeHref="/"
      navigation={navigation.map((item) => ({ ...item, selected: item.page === activePage }))}
      role="student"
      showNotifications
    >
      {children}
    </WorkspaceShell>
  );
}
