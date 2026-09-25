import type { ReactNode } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Avatar } from "@/components/profile/Avatar";
import { Container } from "./Container";
import styles from "./AppShell.module.css";

const navigation = [
  { label: "Início", href: "/", page: "home" },
  { label: "Meus cursos", href: "/meus-cursos", page: "courses" },
  { label: "Explorar", href: "/explorar-cursos", page: "explore" },
  { label: "Materiais", href: "/materiais-complementares", page: "materials" },
  { label: "Certificados", href: "#em-breve" },
  { label: "Meu perfil", href: "/perfil", page: "profile" },
];

export function AppShell({ children, activePage = "home", showSearch = true }: { children: ReactNode; activePage?: "home" | "courses" | "explore" | "materials" | "profile"; showSearch?: boolean }) {
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
          {showSearch && (
            <form action="/pesquisa" className={styles.search} role="search">
              <input aria-label="Buscar cursos e materiais" name="q" placeholder="Buscar cursos e materiais" type="search" />
              <button type="submit">Buscar</button>
            </form>
          )}
          <div className={styles.topbarActions}>
              <button className={styles.iconButton} aria-label="Notificações" type="button">
                Avisos<span className={styles.notificationDot} />
              </button>
            <a className={styles.profileChip} href="/perfil" aria-label="Abrir perfil de Fulano">
              <Avatar />
              <span className={styles.profileCopy}><strong>Fulano</strong><small>Aluno</small></span>
            </a>
          </div>
        </header>
        <main>
          <Container>{children}</Container>
        </main>
      </div>
    </div>
  );
}
