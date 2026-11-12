"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { TeacherShell } from "@/components/teacher/TeacherShell";
import { SimpleScreen } from "@/components/ui/SimpleScreen";
import { demoAccountKey, type DemoAccount } from "@/data/demoAccount";
import { apiFetch, type ApiNotification } from "@/lib/engagementApi";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./page.module.css";

export default function AvisosPage() {
  const router = useRouter();
  const [notices, setNotices] = useState<ApiNotification[]>([]);
  const [errorNotice, setErrorNotice] = useState("");
  const [account] = useDemoStorage<DemoAccount | null>(demoAccountKey, null);
  const isTeacher = account?.role === "teacher";

  useEffect(() => {
    let active = true;
    apiFetch<ApiNotification[]>("/api/notifications")
      .then((data) => {
        if (active) setNotices(data);
      })
      .catch((err) => {
        if (active) {
          setErrorNotice(err instanceof Error ? `Erro ao carregar avisos: ${err.message}` : "Erro ao carregar avisos.");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function openNotice(event: React.MouseEvent<HTMLAnchorElement>, notice: ApiNotification) {
    event.preventDefault();
    try {
      const updated = await apiFetch<{ id: string; is_read: boolean; destination_url: string }>(
        `/api/notifications/${encodeURIComponent(notice.id)}/read`,
        { method: "PATCH" }
      );
      setNotices((prev) =>
        prev.map((item) => (item.id === notice.id ? { ...item, is_read: updated.is_read } : item))
      );
      router.push(updated.destination_url || notice.destination_url);
    } catch (err) {
      setErrorNotice(
        err instanceof Error ? `Erro ao atualizar aviso: ${err.message}` : "Erro ao atualizar aviso."
      );
    }
  }

  const content = (
      <SimpleScreen eyebrow="Sua atividade" title="Avisos" description={isTeacher ? "Novas dúvidas e atualizações dos seus cursos." : "Atualizações que ajudam você a continuar estudando."}>
        {errorNotice && <p role="status">{errorNotice}</p>}
        <section className={styles.list} aria-label="Lista de avisos">
          {notices.map((notice) => (
            <article className={styles.notice} key={notice.id}>
              <div>
                <h2>{notice.title}</h2>
                <p>{notice.description}</p>
                <span>{notice.is_read ? "Lido" : "Novo"}</span>
              </div>
              <a href={notice.destination_url} onClick={(e) => openNotice(e, notice)}>
                Abrir
              </a>
            </article>
          ))}
        </section>
        <p className={styles.demoNote}>Avisos sincronizados com o banco de dados.</p>
      </SimpleScreen>
  );

  return isTeacher ? <TeacherShell activePage="notices">{content}</TeacherShell> : <AppShell>{content}</AppShell>;
}
