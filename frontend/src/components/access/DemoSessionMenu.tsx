"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Avatar } from "@/components/profile/Avatar";
import { demoAccountKey, type DemoAccount, type DemoRole } from "@/data/demoAccount";
import { initialProfile } from "@/data/profile";
import { clearDemoRole } from "@/lib/demoSessionClient";
import { isApiConfigured, logoutFromApi } from "@/lib/apiClient";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./DemoSessionMenu.module.css";

const roleNames: Record<DemoRole, string> = { student: "Aluno", teacher: "Professor", admin: "Administrador" };
const fallbackNames: Record<DemoRole, string> = { student: initialProfile.nickname, teacher: "Prof. Fulano", admin: "Administração" };

export function DemoSessionMenu({ role }: { role: DemoRole }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [account] = useDemoStorage<DemoAccount | null>(demoAccountKey, null);
  const name = account?.role === role ? account.name : fallbackNames[role];

  async function endSession(destination: string) {
    setError("");
    try {
      await logoutFromApi();
      clearDemoRole();
      try { window.localStorage.removeItem(demoAccountKey); } catch { /* The demo still exits without storage. */ }
      router.replace(destination);
      router.refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível encerrar a sessão.");
    }
  }

  return (
    <details className={styles.menu} aria-label={isApiConfigured ? "Conta" : "Conta de demonstração"}>
      <summary className={styles.summary}>
        {role === "student" ? <Avatar /> : <span className={styles.initials} aria-hidden="true">{role === "teacher" ? "PR" : "AD"}</span>}
        <span className={styles.copy}><strong>{name}</strong><small>{roleNames[role]}</small></span>
        <span className={styles.chevron} aria-hidden="true">⌄</span>
      </summary>
      <div className={styles.options}>
        <p>{isApiConfigured ? "Sessão autenticada" : "Perfil de demonstração"}: {roleNames[role]}</p>
        {error && <p role="alert">{error}</p>}
        <Link href="/login" onClick={(event) => { event.preventDefault(); void endSession("/login"); }}>Trocar perfil</Link>
        <button type="button" onClick={() => void endSession("/")}>Sair</button>
      </div>
    </details>
  );
}
