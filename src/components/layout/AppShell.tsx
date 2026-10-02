import type { ReactNode } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { DemoSessionMenu } from "@/components/access/DemoSessionMenu";
import { Container } from "./Container";
import styles from "./AppShell.module.css";

const navigation = [
  { label: "Início", href: "/", page: "home" },
  { label: "Meus cursos", href: "/meus-cursos", page: "courses" },
  { label: "Dúvidas", href: "/duvidas", page: "doubts" },
  { label: "Explorar", href: "/explorar-cursos", page: "explore" },
  { label: "Materiais", href: "/materiais-complementares", page: "materials" },
  { label: "Certificados", href: "/certificados", page: "certificates" },
  { label: "Meu perfil", href: "/perfil", page: "profile" },
];

export function AppShell({ children, activePage = "home", showSearch = true, pageTitle }: { children: ReactNode; activePage?: "home" | "courses" | "doubts" | "explore" | "materials" | "certificates" | "profile"; showSearch?: boolean; pageTitle?: string }) {
  return (
    <div className={styles.appShell}>
      <aside className={styles.sidebar}>
        <Logo />
        <nav className={styles.sidebarNav} aria-label="Navegação principal">
          {navigation.map((item) => (
            <Link
              className={`${styles.navItem} ${item.page ? "" : styles.futureNavItem} ${item.page === activePage ? styles.navItemActive : ""}`}
              href={item.href}
              aria-current={item.page === activePage ? "page" : undefined}
              key={item.label}
            >
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className={styles.sidebarFooter}>
          <a className={styles.navItem} href="#ajuda">
            <span>Ajuda e suporte</span>
          </a>
          <p>Protótipo inicial</p>
        </div>
      </aside>

      <div className={styles.appContent}>
        <header className={styles.topbar}>
          {pageTitle && <strong className={styles.pageTitle}>{pageTitle}</strong>}
          {showSearch && (
            <form action="/pesquisa" className={styles.search} role="search">
              <input aria-label="Buscar cursos e materiais" name="q" placeholder="Buscar cursos e materiais" type="search" />
              <button type="submit">Buscar</button>
            </form>
          )}
          <div className={styles.topbarActions}>
              <Link className={styles.iconButton} aria-label="Notificações" href="/avisos">
                Avisos<span className={styles.notificationDot} />
              </Link>
            <DemoSessionMenu role="student" />
          </div>
        </header>
        <main>
          <Container>{children}</Container>
        </main>
      </div>
    </div>
  );
}
