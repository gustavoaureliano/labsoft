import type { ReactNode } from "react";
import { Logo } from "@/components/brand/Logo";
import { Container } from "@/components/layout/Container";
import shell from "@/components/layout/AppShell.module.css";
import styles from "./TeacherShell.module.css";

export function TeacherShell({ children }: { children: ReactNode }) {
  return (
    <div className={shell.appShell}>
      <aside className={`${shell.sidebar} ${styles.sidebar}`}>
        <Logo />
        <nav className={`${shell.sidebarNav} ${styles.navigation}`} aria-label="Navegação do professor">
          <span className={shell.navItem}>Visão geral</span>
          <span className={shell.navItem}>Meus cursos</span>
          <span className={`${shell.navItem} ${shell.navItemActive}`} aria-current="page">Monetização</span>
          <span className={shell.navItem}>Engajamento</span>
        </nav>
        <div className={shell.sidebarFooter}><p>Área do professor</p></div>
      </aside>

      <div className={shell.appContent}>
        <header className={shell.topbar}>
          <span className={styles.topbarTitle}>Desempenho do professor</span>
          <div className={shell.profileChip}>
            <span className={shell.avatar}>PR</span>
            <span className={shell.profileCopy}><strong>Professor</strong><small>Produtor</small></span>
          </div>
        </header>
        <main><Container>{children}</Container></main>
      </div>
    </div>
  );
}
