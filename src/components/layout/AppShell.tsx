import type { ReactNode } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Avatar } from "@/components/profile/Avatar";
import { initialProfile } from "@/data/profile";
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

export function AppShell({ children, activePage = "home", showSearch = true, account = "student", pageTitle }: { children: ReactNode; activePage?: "home" | "courses" | "doubts" | "explore" | "materials" | "certificates" | "profile"; showSearch?: boolean; account?: "student" | "teacher"; pageTitle?: string }) {
  const accountName = account === "teacher" ? "Prof. Fulano" : initialProfile.nickname;
  const accountSubtitle = account === "teacher" ? "Professor de Física e Biologia" : "Estudante FUVEST";

  return (
    <div className={styles.appShell}>
      <aside className={styles.sidebar}>
        <Logo />
        <nav className={styles.sidebarNav} aria-label="Navegação principal">
          {navigation.map((item) => (
            <Link
              className={`${styles.navItem} ${item.page ? "" : styles.futureNavItem} ${item.page === activePage ? styles.navItemActive : ""}`}
              href={item.page === "doubts" && account === "student" ? "/duvidas/aluno" : item.href}
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
            <details aria-label="Selecionar conta" className={styles.accountMenu}>
              <summary className={styles.profileChip} aria-label="Selecionar conta">
                <Avatar />
                <span className={styles.profileCopy}>
                  <strong>{accountName}</strong>
                  <small>{accountSubtitle}</small>
                </span>
                <span className={styles.accountChevron} aria-hidden="true" />
              </summary>
              <div className={styles.accountOptions}>
                <Link href="/duvidas" aria-current={account === "teacher" ? "true" : undefined}>
                  <Avatar />
                  <span><strong>Prof. Fulano</strong><small>Professor de Física e Biologia</small></span>
                </Link>
                <Link href="/duvidas/aluno" aria-current={account === "student" ? "true" : undefined}>
                  <Avatar />
                  <span><strong>{initialProfile.nickname}</strong><small>Estudante FUVEST</small></span>
                </Link>
              </div>
            </details>
          </div>
        </header>
        <main>
          <Container>{children}</Container>
        </main>
      </div>
    </div>
  );
}
