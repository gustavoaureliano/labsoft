import { cookies } from "next/headers";
import Link from "next/link";
import type { ReactNode } from "react";
import { Logo } from "@/components/brand/Logo";
import { demoRoleCookieName, parseDemoRole, roleHome } from "@/data/demoAccount";
import { AppShell } from "./AppShell";
import styles from "./LearningPageShell.module.css";

export async function LearningPageShell({ children }: { children: ReactNode }) {
  const role = parseDemoRole((await cookies()).get(demoRoleCookieName)?.value);
  if (role === "student") return <AppShell activePage="explore">{children}</AppShell>;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <Logo href={role ? roleHome[role] : "/"} />
        <nav aria-label="Acesso à conta">
          {role ? <Link href={roleHome[role]}>Voltar ao painel</Link> : <><Link href="/login">Entrar</Link><Link className={styles.primary} href="/cadastro">Criar conta</Link></>}
        </nav>
      </header>
      <main className={styles.content}>{children}</main>
      <footer className={styles.footer}>AprovaAí · Protótipo de uma plataforma de estudos</footer>
    </div>
  );
}
