"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { SimpleScreen } from "@/components/ui/SimpleScreen";
import { fetchNotifications, hasApiSession, isApiConfigured, markNotificationAsRead, type ApiNotification } from "@/lib/apiClient";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./page.module.css";

const notices = [
  { id: "lesson", title: "Continue sua aula de Física", description: "Retome Leis de Newton e suas aplicações.", href: "/videoaula" },
  { id: "question", title: "Sua dúvida pode ter uma resposta", description: "Acompanhe suas discussões com os professores.", href: "/duvidas" },
  { id: "courses", title: "Revise seus cursos", description: "Veja o andamento dos seus estudos.", href: "/meus-cursos" },
];

export default function AvisosPage() {
  const [readIds, saveReadIds] = useDemoStorage<string[]>("aprovaai-demo-read-notices", []);
  const [notifications, setNotifications] = useState<ApiNotification[]>([]);
  const [loading, setLoading] = useState(isApiConfigured);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);

  useEffect(() => {
    if (!isApiConfigured) return;

    let active = true;
    Promise.resolve()
      .then(() => {
        if (!hasApiSession()) throw new Error("Entre com sua conta para consultar os avisos.");
        return fetchNotifications();
      })
      .then((items) => {
        if (active) setNotifications(items);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Não foi possível carregar os avisos.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  async function markAsRead(notificationId: string) {
    setSavingId(notificationId);
    setError("");
    try {
      const updated = await markNotificationAsRead(notificationId);
      setNotifications((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível atualizar o aviso.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <AppShell>
      <SimpleScreen eyebrow="Sua atividade" title="Avisos" description="Atualizações que ajudam você a continuar estudando.">
        {isApiConfigured ? (
          <>
            {error && <p className={styles.error} role="alert">{error}{!hasApiSession() && <> <Link href="/login">Entrar</Link></>}</p>}
            {loading ? <p role="status">Carregando avisos...</p> : notifications.length > 0 ? (
              <section className={styles.list} aria-label="Lista de avisos">
                {notifications.map((notification) => (
                  <article className={`${styles.notice} ${notification.read_at ? styles.read : ""}`} key={notification.id}>
                    <div>
                      <h2>{notification.message}</h2>
                      <p>{notification.category.replaceAll("_", " ")}</p>
                      <time dateTime={notification.created_at}>{new Date(notification.created_at).toLocaleString("pt-BR")}</time>
                      <span>{notification.read_at ? "Lido" : "Novo"}</span>
                    </div>
                    <button type="button" disabled={Boolean(notification.read_at) || savingId === notification.id} onClick={() => markAsRead(notification.id)}>
                      {notification.read_at ? "Lido" : savingId === notification.id ? "Salvando..." : "Marcar como lido"}
                    </button>
                  </article>
                ))}
              </section>
            ) : !error && <p className={styles.demoNote}>Você não tem avisos no momento.</p>}
          </>
        ) : (
          <>
            <section className={styles.list} aria-label="Lista de avisos">
              {notices.map((notice) => (
                <article className={styles.notice} key={notice.id}>
                  <div><h2>{notice.title}</h2><p>{notice.description}</p><span>{readIds.includes(notice.id) ? "Lido" : "Novo"}</span></div>
                  <Link href={notice.href} onClick={() => saveReadIds([...new Set([...readIds, notice.id])])}>Abrir</Link>
                </article>
              ))}
            </section>
            <p className={styles.demoNote}>Avisos ilustrativos. O estado de leitura fica somente neste navegador.</p>
          </>
        )}
      </SimpleScreen>
    </AppShell>
  );
}
