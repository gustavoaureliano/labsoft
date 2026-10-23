"use client";

import { useEffect, useState } from "react";
import { teacherApplicationKey, type TeacherApplication } from "@/data/demoAccount";
import { apiFetch, type ApiModerationQueueItem } from "@/lib/engagementApi";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { AdminShell } from "./AdminShell";
import styles from "./ModerationDashboard.module.css";

const initialTeachers = [
  {
    id: 1,
    initials: "AR",
    name: "Ana Beatriz Ribeiro",
    area: "Filosofia e Sociologia",
    detail: "Documentação completa",
    submittedAt: "Enviado há 2 horas",
  },
  {
    id: 2,
    initials: "RM",
    name: "Rafael Moreira",
    area: "Física",
    detail: "Diploma e identidade verificados",
    submittedAt: "Enviado há 5 horas",
  },
  {
    id: 3,
    initials: "CM",
    name: "Carla Mendes",
    area: "Língua Portuguesa e Redação",
    detail: "Aguardando análise cadastral",
    submittedAt: "Enviado ontem",
  },
];

const blockedComments = [
  {
    author: "Lucas N.",
    excerpt: "Comentário ocultado automaticamente por linguagem ofensiva.",
    reason: "Linguagem imprópria",
    time: "Há 18 min",
  },
  {
    author: "Marina S.",
    excerpt: "Mensagem com possível divulgação de dados pessoais.",
    reason: "Dados pessoais",
    time: "Há 1 h",
  },
  {
    author: "Pedro A.",
    excerpt: "Comentário repetido em diferentes aulas do mesmo curso.",
    reason: "Spam",
    time: "Há 3 h",
  },
];

const reportedContent = [
  {
    title: "Aula 04 · Ética e sociedade",
    course: "Introdução à Filosofia",
    reason: "Informação possivelmente incorreta",
    reports: 4,
  },
  {
    title: "Material complementar · Campo elétrico",
    course: "Eletrodinâmica",
    reason: "Arquivo indisponível",
    reports: 3,
  },
  {
    title: "Aula 07 · Estrutura da redação",
    course: "Redação Nota 1000",
    reason: "Conteúdo desatualizado",
    reports: 2,
  },
];

export function ModerationDashboard() {
  const [teachers, setTeachers] = useState(initialTeachers);
  const [application, saveApplication] = useDemoStorage<TeacherApplication | null>(teacherApplicationKey, null);
  const [approvedTeacher, setApprovedTeacher] = useState<string | null>(null);
  const [apiQueue, setApiQueue] = useState<ApiModerationQueueItem[]>([]);
  const [decidedItems, setDecidedItems] = useState<Record<string, "mantido" | "ocultado">>({});
  const [errorNotice, setErrorNotice] = useState("");

  useEffect(() => {
    let active = true;
    apiFetch<ApiModerationQueueItem[]>("/api/moderation/queue")
      .then((data) => {
        if (active) setApiQueue(data);
      })
      .catch((err) => {
        if (active) {
          setErrorNotice(err instanceof Error ? `Erro ao carregar fila de moderação: ${err.message}` : "Erro ao carregar fila de moderação.");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  function approveTeacher(id: number) {
    const teacher = teachers.find((item) => item.id === id);
    if (!teacher) return;

    setTeachers((current) => current.filter((item) => item.id !== id));
    setApprovedTeacher(teacher.name);
  }

  function reviewApplication(status: "approved" | "rejected") {
    if (!application) return;
    saveApplication({ ...application, status });
    setApprovedTeacher(status === "approved" ? application.name : null);
  }

  async function applyDecision(
    itemId: string,
    itemType: "lesson" | "course" | "comment",
    decision: "mantido" | "ocultado"
  ) {
    const apiDecision = decision === "mantido" ? "keep" : "hide";
    setErrorNotice("");
    try {
      await apiFetch(`/api/moderation/queue/${encodeURIComponent(itemId)}/decision`, {
        method: "POST",
        body: JSON.stringify({
          item_type: itemType,
          decision: apiDecision,
          justification: `Decisão administrativa via painel: ${decision}`,
        }),
      });
      setDecidedItems((prev) => ({ ...prev, [`${itemType}:${itemId}`]: decision }));
    } catch (err) {
      setErrorNotice(
        err instanceof Error ? `Erro ao aplicar decisão: ${err.message}` : "Erro ao aplicar decisão."
      );
    }
  }

  const pendingApplication = application?.status === "pending" ? application : null;
  const apiCommentItems = apiQueue.filter((item) => item.item_type === "comment");
  const apiContentItems = apiQueue.filter((item) => item.item_type !== "comment");

  return (
    <AdminShell activePage="moderation" topbarTitle="Segurança e qualidade da plataforma">
      <div className={styles.dashboard}>
        <header className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>Gestão de comunidade</span>
            <h1>Moderação e qualidade</h1>
            <p>Analise cadastros, comentários e conteúdos sinalizados pela comunidade.</p>
          </div>
          <span className={styles.demoBadge}>Fila do banco de dados</span>
        </header>

        {errorNotice && <p role="status">{errorNotice}</p>}

        {approvedTeacher ? (
          <div className={styles.successNotice} role="status">
            <strong>{approvedTeacher}</strong> foi aprovado para publicar cursos.
          </div>
        ) : null}

        <section className={styles.metrics} aria-label="Resumo das filas de moderação">
          <article className={styles.metricCard}>
            <span>Professores pendentes</span>
            <strong>{teachers.length + (pendingApplication ? 1 : 0)}</strong>
            <p>Cadastros aguardando aprovação</p>
          </article>
          <article className={styles.metricCard}>
            <span>Comentários bloqueados</span>
            <strong>{blockedComments.length + apiCommentItems.length}</strong>
            <p>Mensagens retidas pelos filtros</p>
          </article>
          <article className={styles.metricCard}>
            <span>Conteúdos reportados</span>
            <strong>
              {reportedContent.length + apiContentItems.filter((i) => !decidedItems[`${i.item_type}:${i.item_id}`]).length}
            </strong>
            <p>Aguardando análise da equipe</p>
          </article>
        </section>

        <section className={styles.panel} aria-labelledby="teachers-title">
          <div className={styles.panelHeader}>
            <div>
              <span className={styles.eyebrow}>Fila de aprovação</span>
              <h2 id="teachers-title">Professores para aprovar</h2>
              <p>Confira as informações cadastrais antes de liberar a publicação de cursos.</p>
            </div>
            <span className={styles.countBadge}>{teachers.length + (pendingApplication ? 1 : 0)} pendentes</span>
          </div>

          {teachers.length ? (
            <ul className={styles.teacherList}>
              {teachers.map((teacher) => (
                <li className={styles.teacherItem} key={teacher.id}>
                  <span className={styles.teacherAvatar} aria-hidden="true">{teacher.initials}</span>
                  <span className={styles.teacherInfo}>
                    <strong>{teacher.name}</strong>
                    <small>{teacher.area}</small>
                  </span>
                  <span className={styles.teacherStatus}>
                    <strong>{teacher.detail}</strong>
                    <small>{teacher.submittedAt}</small>
                  </span>
                  <button className={styles.approveButton} type="button" onClick={() => approveTeacher(teacher.id)}>
                    Aprovar
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className={styles.emptyState}>Todos os professores da fila foram analisados.</p>
          )}
          {pendingApplication && <div className={styles.teacherItem}>
            <span className={styles.teacherAvatar} aria-hidden="true">{pendingApplication.name.slice(0, 2).toUpperCase()}</span>
            <span className={styles.teacherInfo}><strong>{pendingApplication.name}</strong><small>{pendingApplication.area}</small></span>
            <span className={styles.teacherStatus}><strong>Solicitação de demonstração</strong><small>Enviada neste navegador</small></span>
            <span className={styles.teacherActions}>
              <button className={styles.approveButton} type="button" onClick={() => reviewApplication("approved")}>Aprovar</button>
              <button className={styles.approveButton} type="button" onClick={() => reviewApplication("rejected")}>Recusar</button>
            </span>
          </div>}
        </section>

        <div className={styles.reviewGrid}>
          <section className={styles.panel} aria-labelledby="comments-title">
            <div className={styles.panelHeader}>
              <div>
                <span className={styles.eyebrow}>Comunidade</span>
                <h2 id="comments-title">Comentários bloqueados</h2>
                <p>Mensagens retidas para revisão manual.</p>
              </div>
              <span className={styles.countBadge}>{blockedComments.length + apiCommentItems.length}</span>
            </div>
            <ul className={styles.reviewList}>
              {apiCommentItems.map((item) => {
                const decided = decidedItems[`comment:${item.item_id}`];
                return (
                  <li className={styles.reviewItem} key={item.queue_id}>
                    <div className={styles.reviewMeta}>
                      <strong>{item.author_or_owner}</strong>
                      <small>Retido no banco</small>
                    </div>
                    <p>{item.title_or_excerpt}</p>
                    <span className={styles.reasonBadge}>{item.reasons[0] ?? "Filtro automático"}</span>
                    {decided ? (
                      <p role="status">Decisão registrada neste navegador: comentário {decided}.</p>
                    ) : (
                      <div className={styles.reviewActions}>
                        <button type="button" onClick={() => applyDecision(item.item_id, "comment", "mantido")}>Manter comentário</button>
                        <button type="button" onClick={() => applyDecision(item.item_id, "comment", "ocultado")}>Ocultar comentário</button>
                      </div>
                    )}
                  </li>
                );
              })}
              {blockedComments.map((comment) => (
                <li className={styles.reviewItem} key={`${comment.author}-${comment.reason}`}>
                  <div className={styles.reviewMeta}>
                    <strong>{comment.author}</strong>
                    <small>{comment.time}</small>
                  </div>
                  <p>{comment.excerpt}</p>
                  <span className={styles.reasonBadge}>{comment.reason}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className={styles.panel} aria-labelledby="reports-title">
            <div className={styles.panelHeader}>
              <div>
                <span className={styles.eyebrow}>Qualidade do conteúdo</span>
                <h2 id="reports-title">Conteúdos reportados</h2>
                <p>Materiais à espera de análise.</p>
              </div>
              <span className={styles.countBadge}>
                {reportedContent.length + apiContentItems.filter((i) => !decidedItems[`${i.item_type}:${i.item_id}`]).length}
              </span>
            </div>
            <ul className={styles.reviewList}>
              {apiContentItems.map((item) => {
                const decided = decidedItems[`${item.item_type}:${item.item_id}`];
                return (
                  <li className={styles.reviewItem} key={item.queue_id}>
                    <div className={styles.reviewMeta}>
                      <strong>{item.title_or_excerpt}</strong>
                      <small>{item.reports_count} {item.reports_count === 1 ? "denúncia" : "denúncias"}</small>
                    </div>
                    <p>{item.author_or_owner}</p>
                    <span className={styles.reasonBadge}>{item.reasons[0]}</span>
                    {decided ? (
                      <p role="status">Decisão registrada neste navegador: conteúdo {decided}.</p>
                    ) : (
                      <div className={styles.reviewActions}>
                        <button type="button" onClick={() => applyDecision(item.item_id, item.item_type, "mantido")}>Manter conteúdo</button>
                        <button type="button" onClick={() => applyDecision(item.item_id, item.item_type, "ocultado")}>Ocultar conteúdo</button>
                      </div>
                    )}
                  </li>
                );
              })}
              {reportedContent.map((content) => (
                <li className={styles.reviewItem} key={content.title}>
                  <div className={styles.reviewMeta}>
                    <strong>{content.title}</strong>
                    <small>{content.reports} denúncias</small>
                  </div>
                  <p>{content.course}</p>
                  <span className={styles.reasonBadge}>{content.reason}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </AdminShell>
  );
}
