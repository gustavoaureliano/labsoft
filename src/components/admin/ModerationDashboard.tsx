"use client";

import { useState } from "react";
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
  const [approvedTeacher, setApprovedTeacher] = useState<string | null>(null);

  function approveTeacher(id: number) {
    const teacher = teachers.find((item) => item.id === id);
    if (!teacher) return;

    setTeachers((current) => current.filter((item) => item.id !== id));
    setApprovedTeacher(teacher.name);
  }

  return (
    <AdminShell activePage="moderation" topbarTitle="Segurança e qualidade da plataforma">
      <div className={styles.dashboard}>
        <header className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>Gestão de comunidade</span>
            <h1>Moderação e qualidade</h1>
            <p>Analise cadastros, comentários e conteúdos sinalizados pela comunidade.</p>
          </div>
          <span className={styles.demoBadge}>Dados ilustrativos</span>
        </header>

        {approvedTeacher ? (
          <div className={styles.successNotice} role="status">
            <strong>{approvedTeacher}</strong> foi aprovado para publicar cursos.
          </div>
        ) : null}

        <section className={styles.metrics} aria-label="Resumo das filas de moderação">
          <article className={styles.metricCard}>
            <span>Professores pendentes</span>
            <strong>{teachers.length}</strong>
            <p>Cadastros aguardando aprovação</p>
          </article>
          <article className={styles.metricCard}>
            <span>Comentários bloqueados</span>
            <strong>{blockedComments.length}</strong>
            <p>Mensagens retidas pelos filtros</p>
          </article>
          <article className={styles.metricCard}>
            <span>Conteúdos reportados</span>
            <strong>{reportedContent.length}</strong>
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
            <span className={styles.countBadge}>{teachers.length} pendentes</span>
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
        </section>

        <div className={styles.reviewGrid}>
          <section className={styles.panel} aria-labelledby="comments-title">
            <div className={styles.panelHeader}>
              <div>
                <span className={styles.eyebrow}>Comunidade</span>
                <h2 id="comments-title">Comentários bloqueados</h2>
                <p>Mensagens retidas para revisão manual.</p>
              </div>
              <span className={styles.countBadge}>{blockedComments.length}</span>
            </div>
            <ul className={styles.reviewList}>
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
              <span className={styles.countBadge}>{reportedContent.length}</span>
            </div>
            <ul className={styles.reviewList}>
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
