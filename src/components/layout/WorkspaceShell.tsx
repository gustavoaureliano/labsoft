"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { DemoSessionMenu } from "@/components/access/DemoSessionMenu";
import type { DemoRole } from "@/data/demoAccount";
import { Container } from "./Container";
import { NavIcon, type NavIconName } from "./NavIcon";
import { useWorkspaceSidebar } from "./WorkspaceSidebarState";
import styles from "./WorkspaceShell.module.css";

type NavigationItem = {
  href: string;
  icon: NavIconName;
  label: string;
  selected: boolean;
};

type Header = { type: "search" } | { type: "title"; title: string };

export function WorkspaceShell({
  children,
  contentWidth = "default",
  footer,
  header,
  homeHref,
  navigation,
  role,
  showNotifications = false,
}: {
  children: ReactNode;
  contentWidth?: "default" | "wide";
  footer: string;
  header: Header;
  homeHref: string;
  navigation: NavigationItem[];
  role: DemoRole;
  showNotifications?: boolean;
}) {
  const { animate, collapsed, toggle } = useWorkspaceSidebar();
  const navigationId = `${role}-navigation`;
  const navigationLabel = role === "student" ? "Navegação principal" : role === "teacher" ? "Navegação do professor" : "Navegação administrativa";

  return (
    <div className={`${styles.shell} ${header.type === "search" ? styles.searchHeader : ""} ${collapsed ? styles.collapsed : ""} ${animate ? styles.canAnimate : ""}`}>
      <header className={styles.topbar}>
        <div className={styles.brandGroup}>
          <button className={styles.toggle} type="button" onClick={toggle} aria-controls={navigationId} aria-expanded={!collapsed} aria-label={collapsed ? "Expandir menu" : "Recolher menu"} title={collapsed ? "Expandir menu" : "Recolher menu"}>
            <NavIcon name={collapsed ? "expand" : "collapse"} />
          </button>
          <Logo href={homeHref} />
        </div>

        {header.type === "search" ? (
          <form action="/pesquisa" className={styles.search} role="search">
            <input aria-label="Buscar cursos e materiais" name="q" placeholder="Buscar cursos e materiais" type="search" />
            <button type="submit">Buscar</button>
          </form>
        ) : <span className={styles.title}>{header.title}</span>}

        <div className={styles.account}>
          {showNotifications && <Link className={styles.notificationLink} aria-label="Notificações" href="/avisos">Avisos<span className={styles.notificationDot} /></Link>}
          <DemoSessionMenu role={role} />
        </div>
      </header>

      <aside className={styles.sidebar}>
        <nav className={styles.navigation} id={navigationId} aria-label={navigationLabel}>
          {navigation.map((item) => (
            <Link className={`${styles.navItem} ${item.selected ? styles.navItemActive : ""}`} href={item.href} aria-current={item.selected ? "page" : undefined} aria-label={item.label} title={collapsed ? item.label : undefined} key={item.href}>
              <NavIcon name={item.icon} /><span className={styles.navLabel}>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className={styles.footer}><p>{footer}</p></div>
      </aside>

      <div className={styles.content}><main><Container className={contentWidth === "wide" ? styles.wideContainer : ""}>{children}</Container></main></div>
    </div>
  );
}
