import type { ReactNode } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Container } from "@/components/layout/Container";
import shell from "@/components/layout/AppShell.module.css";
import styles from "./AdminShell.module.css";

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
    <div className={shell.appShell}>
      <aside className={shell.sidebar}>
        <Logo />
        <nav className={shell.sidebarNav} aria-label="Navegação administrativa">
          <Link
            className={`${shell.navItem} ${activePage === "overview" ? shell.navItemActive : ""}`}
            href="/admin"
            aria-current={activePage === "overview" ? "page" : undefined}
          >
            Visão geral
          </Link>
          <Link
            className={`${shell.navItem} ${activePage === "moderation" ? shell.navItemActive : ""}`}
            href="/admin/moderacao"
            aria-current={activePage === "moderation" ? "page" : undefined}
          >
            Moderação
          </Link>
        </nav>
        <div className={shell.sidebarFooter}>
          <p>Ambiente administrativo</p>
        </div>
      </aside>

      <div className={shell.appContent}>
        <header className={shell.topbar}>
          <span className={styles.topbarTitle}>{topbarTitle}</span>
          <div className={shell.profileChip}>
            <span className={styles.adminAvatar}>AD</span>
            <span className={shell.profileCopy}>
              <strong>Administração</strong>
              <small>Gestão</small>
            </span>
          </div>
        </header>
        <main>
          <Container>{children}</Container>
        </main>
      </div>
    </div>
  );
}
