import type { ReactNode } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Container } from "./Container";
import styles from "./AppShell.module.css";

const navigation = [
  { label: "Início", href: "/", page: "home" },
  { label: "Meus cursos", href: "/meus-cursos", page: "courses" },
  { label: "Explorar", href: "/explorar-cursos", page: "explore" },
  { label: "Materiais", href: "/materiais-complementares", page: "materials" },
  { label: "Certificados", href: "#em-breve" },
  { label: "Meu perfil", href: "#em-breve" },
];

export function AppShell({ children, activePage = "home" }: { children: ReactNode; activePage?: "home" | "courses" | "explore" | "materials" }) {
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
          <form action="/pesquisa" className={styles.search} role="search">
            <input aria-label="Buscar" name="q" placeholder="Buscar cursos e materiais" type="search" />
            <button type="submit">Buscar</button>
          </form>
          <div className={styles.topbarActions}>
            <button className={styles.iconButton} aria-label="Notificações" type="button">
              Avisos<span className={styles.notificationDot} />
            </button>
            <div className={styles.profileChip}>
              <span className={styles.avatar}>FU</span>
              <span className={styles.profileCopy}><strong>Fulano</strong><small>Aluno</small></span>
            </div>
          </div>
        </header>
        <main>
          <Container>{children}</Container>
        </main>
      </div>
    </div>
  );
}
