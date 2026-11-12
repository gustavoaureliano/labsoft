"use client";

import { useEffect, useState } from "react";
import { findDemoCourse } from "@/data/demoCourses";
import { apiFetch, type ApiTeacherAnalytics } from "@/lib/engagementApi";
import { isApiConfigured } from "@/lib/apiClient";
import { TeacherShell } from "./TeacherShell";
import styles from "./TeacherMonetization.module.css";

const revenue = [
  { month: "Abr", value: 5800 },
  { month: "Mai", value: 6420 },
  { month: "Jun", value: 7100 },
  { month: "Jul", value: 7650 },
  { month: "Ago", value: 8340 },
  { month: "Set", value: 9240 },
];

const courses = [
  { title: findDemoCourse("fisica-quantica")!.title, students: 924, revenue: "R$ 9.240", share: "100%" },
  { title: findDemoCourse("fisica-enem-mecanica")!.title, students: 6000, revenue: "R$ 0", share: "0%" },
];

const maximumRevenue = Math.max(...revenue.map((item) => item.value));

type Period = ApiTeacherAnalytics["period"];
type CourseOption = { course_id: string; course_title: string };

const periodLabels: Record<Period, string> = { "30d": "Últimos 30 dias", "90d": "Últimos 90 dias", "365d": "Últimos 365 dias" };

function formatNumber(value: number | null | undefined, digits = 0) {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function formatPercent(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : `${formatNumber(value, 1)}%`;
}

function TeacherEngagementReport() {
  const [period, setPeriod] = useState<Period>("30d");
  const [courseId, setCourseId] = useState("");
  const [courseOptions, setCourseOptions] = useState<CourseOption[]>([]);
  const query = new URLSearchParams({ period });
  if (courseId) query.set("course_id", courseId);
  const path = `/api/analytics/teacher?${query}`;
  const [result, setResult] = useState<{ path: string; data?: ApiTeacherAnalytics; error?: string } | null>(null);

  useEffect(() => {
    let active = true;
    apiFetch<ApiTeacherAnalytics>(path)
      .then((data) => {
        if (!active) return;
        setResult({ path, data });
        if (data.course_id === null) setCourseOptions(data.courses.map(({ course_id, course_title }) => ({ course_id, course_title })));
      })
      .catch((error) => {
        if (active) setResult({ path, error: error instanceof Error ? error.message : "Erro desconhecido" });
      });
    return () => {
      active = false;
    };
  }, [path]);

  const current = result?.path === path ? result : null;
  const analytics = current?.data ?? null;
  const totalRatings = analytics?.total_ratings.value ?? null;
  const indicators = [
    { label: "Taxa de conclusão", value: formatPercent(analytics?.completion_rate.value), indicator: analytics?.completion_rate },
    { label: "Alunos ativos", value: formatNumber(analytics?.active_students.value), indicator: analytics?.active_students },
    { label: "Matrículas", value: formatNumber(analytics?.enrollments.value), indicator: analytics?.enrollments },
    {
      label: "Avaliação média",
      value: analytics && totalRatings ? `${formatNumber(analytics.average_rating.value, 1)}/5` : "—",
      note: totalRatings === null ? undefined : `com ${totalRatings} ${totalRatings === 1 ? "avaliação" : "avaliações"}`,
      indicator: analytics?.average_rating,
    },
    { label: "Dúvidas respondidas", value: formatPercent(analytics?.question_response_rate.value), indicator: analytics?.question_response_rate },
  ];

  return (
    <>
      <section className={styles.card} aria-labelledby="engagement-title">
        <div className={styles.cardHeader}>
          <div><span className={styles.eyebrow}>Engajamento</span><h2 id="engagement-title">Atividade dos alunos</h2></div>
        </div>
        <div className={styles.filters}>
          <label>Período
            <select value={period} onChange={(event) => setPeriod(event.target.value as Period)}>
              {(Object.keys(periodLabels) as Period[]).map((value) => <option key={value} value={value}>{periodLabels[value]}</option>)}
            </select>
          </label>
          <label>Curso
            <select value={courseId} onChange={(event) => setCourseId(event.target.value)}>
              <option value="">Todos os cursos</option>
              {courseOptions.map((course) => <option key={course.course_id} value={course.course_id}>{course.course_title}</option>)}
            </select>
          </label>
        </div>
        {!current && <p role="status">Carregando indicadores...</p>}
        {current?.error && <p role="alert">Não foi possível carregar os indicadores: {current.error}</p>}
        <dl className={styles.engagement}>
          {indicators.map((item) => (
            <div key={item.label}>
              <dt>{item.label}</dt>
              <dd>{item.value}</dd>
              {item.note && <small>{item.note}</small>}
              {item.indicator && <small className={styles.source}>{item.indicator.description} · Fonte: {item.indicator.source}</small>}
            </div>
          ))}
        </dl>
      </section>
      {analytics && analytics.courses.length > 0 && (
        <section className={`${styles.card} ${styles.coursesCard}`} aria-labelledby="course-engagement-title">
          <div className={styles.cardHeader}>
            <div><span className={styles.eyebrow}>Indicadores por curso</span><h2 id="course-engagement-title">Engajamento por curso</h2></div>
          </div>
          <div className={styles.tableWrap}>
            <table>
              <thead><tr><th>Curso</th><th>Matrículas</th><th>Alunos ativos</th><th>Conclusão</th><th>Tempo médio</th><th>Avaliação</th><th>Dúvidas pendentes</th></tr></thead>
              <tbody>{analytics.courses.map((course) => (
                <tr key={course.course_id}>
                  <td><strong>{course.course_title}</strong></td>
                  <td>{formatNumber(course.enrollments)}</td>
                  <td>{formatNumber(course.active_students)}</td>
                  <td>{formatPercent(course.completion_rate)}</td>
                  <td>{course.avg_watch_minutes === null ? "—" : `${course.avg_watch_minutes} min`}</td>
                  <td>{course.total_ratings ? `${formatNumber(course.average_rating, 1)}/5` : "—"}</td>
                  <td>{course.pending_questions}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}

export function TeacherMonetization() {
  if (isApiConfigured) return <TeacherShell><div className={styles.page}>
    <header className={styles.heading}><div><h1>Monetização e desempenho</h1>
      <p>Relatórios financeiros e repasses docentes ainda não estão disponíveis no modo integrado.</p></div></header>
    <p>O PSP atual é simulado. Heartbeats não comprovam tempo assistido e não são base para repasses.</p>
    <TeacherEngagementReport />
  </div></TeacherShell>;

  return (
    <TeacherShell>
      <div className={styles.page}>
        <header className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>Relatórios do professor</span>
            <h1>Monetização e desempenho</h1>
            <p>Acompanhe receitas, pagamentos e o engajamento dos seus alunos.</p>
          </div>
          <span className={styles.period}>Dados financeiros demonstrativos</span>
        </header>

        <section className={styles.metrics} aria-label="Resumo financeiro">
          <article><span>Receita mensal</span><strong>R$ 9.240</strong><p><b>+10,8%</b> sobre o mês anterior</p></article>
          <article><span>Saldo disponível</span><strong>R$ 7.890</strong><p>Próximo repasse em 5 dias</p></article>
          <article><span>Alunos pagantes</span><strong>924</strong><p><b>+68</b> novas matrículas</p></article>
        </section>

        <section className={styles.card} aria-labelledby="revenue-title">
          <div className={styles.cardHeader}>
            <div><span className={styles.eyebrow}>Relatório financeiro</span><h2 id="revenue-title">Evolução da receita</h2></div>
            <strong>R$ 44.550</strong>
          </div>
          <ol className={styles.chart} aria-label="Receita dos últimos seis meses">
            {revenue.map((item) => (
              <li key={item.month}>
                <span className={styles.chartValue}>R$ {(item.value / 1000).toFixed(1)}k</span>
                <div><i style={{ height: `${(item.value / maximumRevenue) * 100}%` }} /></div>
                <span>{item.month}</span>
              </li>
            ))}
          </ol>
        </section>

        <TeacherEngagementReport />

        <section className={`${styles.card} ${styles.coursesCard}`} aria-labelledby="courses-title">
          <div className={styles.cardHeader}>
            <div><span className={styles.eyebrow}>Desempenho por produto</span><h2 id="courses-title">Receita por curso</h2></div>
            <span className={styles.status}>Atualizado hoje</span>
          </div>
          <div className={styles.tableWrap}>
            <table>
              <thead><tr><th>Curso</th><th>Alunos</th><th>Receita</th><th>Participação</th></tr></thead>
              <tbody>{courses.map((course) => <tr key={course.title}><td><strong>{course.title}</strong></td><td>{course.students}</td><td>{course.revenue}</td><td>{course.share}</td></tr>)}</tbody>
            </table>
          </div>
        </section>
      </div>
    </TeacherShell>
  );
}
