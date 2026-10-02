"use client";

import Link from "next/link";
import { teacherApplicationKey, type TeacherApplication } from "@/data/demoAccount";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./AccessPage.module.css";

export function TeacherApplicationStatus() {
  const [application] = useDemoStorage<TeacherApplication | null>(teacherApplicationKey, null);
  const status = application?.status;

  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="application-title">
        <h1 id="application-title">Solicitação de professor</h1>
        {application ? (
          <>
            <p className={styles.description}>{application.name} · {application.area}</p>
            <p className={styles.notice} role="status">{status === "approved" ? "Cadastro aprovado nesta demonstração." : status === "rejected" ? "Cadastro recusado nesta demonstração." : "Cadastro enviado e aguardando análise nesta demonstração."}</p>
            {status === "approved" ? <Link className={styles.primaryButton} href="/professor/cursos">Abrir área do professor</Link> : <Link href="/cadastro/professor">Enviar outra solicitação</Link>}
          </>
        ) : <><p className={styles.description}>Nenhuma solicitação foi enviada neste navegador.</p><Link href="/cadastro/professor">Solicitar cadastro</Link></>}
        <Link href="/">Voltar ao início</Link>
      </section>
    </main>
  );
}
