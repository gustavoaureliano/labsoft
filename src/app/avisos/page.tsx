"use client";

import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { SimpleScreen } from "@/components/ui/SimpleScreen";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./page.module.css";

const notices = [
  { id: "lesson", title: "Continue sua aula de Física", description: "Retome Leis de Newton e suas aplicações.", href: "/videoaula" },
  { id: "question", title: "Sua dúvida pode ter uma resposta", description: "Acompanhe suas discussões com os professores.", href: "/duvidas/aluno" },
  { id: "courses", title: "Revise seus cursos", description: "Veja o andamento dos seus estudos.", href: "/meus-cursos" },
];

export default function AvisosPage() {
  const [readIds, saveReadIds] = useDemoStorage<string[]>("aprovaai-demo-read-notices", []);

  return (
    <AppShell>
      <SimpleScreen eyebrow="Sua atividade" title="Avisos" description="Atualizações que ajudam você a continuar estudando.">
        <section className={styles.list} aria-label="Lista de avisos">
          {notices.map((notice) => (
            <article className={styles.notice} key={notice.id}>
              <div><h2>{notice.title}</h2><p>{notice.description}</p><span>{readIds.includes(notice.id) ? "Lido" : "Novo"}</span></div>
              <Link href={notice.href} onClick={() => saveReadIds([...new Set([...readIds, notice.id])])}>Abrir</Link>
            </article>
          ))}
        </section>
        <p className={styles.demoNote}>Avisos ilustrativos. O estado de leitura fica somente neste navegador.</p>
      </SimpleScreen>
    </AppShell>
  );
}
