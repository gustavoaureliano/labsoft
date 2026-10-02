"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Avatar } from "@/components/profile/Avatar";
import { demoAccountKey, type DemoAccount, type DemoRole } from "@/data/demoAccount";
import { initialProfile } from "@/data/profile";
import { clearDemoRole } from "@/lib/demoSessionClient";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./DemoSessionMenu.module.css";

const roleNames: Record<DemoRole, string> = { student: "Aluno", teacher: "Professor", admin: "Administrador" };
const fallbackNames: Record<DemoRole, string> = { student: initialProfile.nickname, teacher: "Prof. Fulano", admin: "Administração" };

export function DemoSessionMenu({ role }: { role: DemoRole }) {
  const router = useRouter();
  const [account] = useDemoStorage<DemoAccount | null>(demoAccountKey, null);
  const name = account?.role === role ? account.name : fallbackNames[role];

  function signOut() {
    clearDemoRole();
    try { window.localStorage.removeItem(demoAccountKey); } catch { /* The demo still exits without storage. */ }
    router.replace("/login");
    router.refresh();
  }

  return (
    <details className={styles.menu} aria-label="Conta de demonstração">
      <summary className={styles.summary}>
        {role === "student" ? <Avatar /> : <span className={styles.initials} aria-hidden="true">{role === "teacher" ? "PR" : "AD"}</span>}
        <span className={styles.copy}><strong>{name}</strong><small>{roleNames[role]}</small></span>
        <span className={styles.chevron} aria-hidden="true">⌄</span>
      </summary>
      <div className={styles.options}>
        <p>Perfil de demonstração: {roleNames[role]}</p>
        <Link href="/login" onClick={clearDemoRole}>Trocar perfil</Link>
        <button type="button" onClick={signOut}>Sair</button>
      </div>
    </details>
  );
}
