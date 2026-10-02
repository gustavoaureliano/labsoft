import type { ReactNode } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { DemoSessionMenu } from "@/components/access/DemoSessionMenu";
import { Container } from "@/components/layout/Container";
import shell from "@/components/layout/AppShell.module.css";
import styles from "./TeacherShell.module.css";

export function TeacherShell({ children, activePage = "monetization" }: { children: ReactNode; activePage?: "courses" | "doubts" | "monetization" }) {
  return (
    <div className={shell.appShell}>
      <aside className={`${shell.sidebar} ${styles.sidebar}`}>
        <Logo href="/professor/cursos" />
        <nav className={`${shell.sidebarNav} ${styles.navigation}`} aria-label="Navegação do professor">
          <Link className={`${shell.navItem} ${activePage === "courses" ? shell.navItemActive : ""}`} href="/professor/cursos" aria-current={activePage === "courses" ? "page" : undefined}>Meus cursos</Link>
          <Link className={`${shell.navItem} ${activePage === "doubts" ? shell.navItemActive : ""}`} href="/professor/duvidas" aria-current={activePage === "doubts" ? "page" : undefined}>Dúvidas</Link>
          <Link className={`${shell.navItem} ${activePage === "monetization" ? shell.navItemActive : ""}`} href="/professor/monetizacao" aria-current={activePage === "monetization" ? "page" : undefined}>Monetização</Link>
        </nav>
        <div className={shell.sidebarFooter}><p>Área do professor</p></div>
      </aside>

      <div className={shell.appContent}>
        <header className={shell.topbar}>
          <span className={styles.topbarTitle}>{activePage === "courses" ? "Gestão de cursos" : activePage === "doubts" ? "Dúvidas dos alunos" : "Desempenho do professor"}</span>
          <DemoSessionMenu role="teacher" />
        </header>
        <main><Container>{children}</Container></main>
      </div>
    </div>
  );
}
