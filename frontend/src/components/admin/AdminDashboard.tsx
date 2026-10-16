"use client";

import { useState } from "react";
import { AdminShell } from "./AdminShell";
import styles from "./AdminDashboard.module.css";

type AccessPeriod = "monthly" | "annual";

const accessData: Record<AccessPeriod, { label: string; count: number }[]> = {
  monthly: [
    { label: "Semana 1", count: 5460 },
    { label: "Semana 2", count: 6320 },
    { label: "Semana 3", count: 7180 },
    { label: "Semana 4", count: 7560 },
  ],
  annual: [
    { label: "Jan", count: 14200 },
    { label: "Fev", count: 15800 },
    { label: "Mar", count: 17300 },
    { label: "Abr", count: 16900 },
    { label: "Mai", count: 19100 },
    { label: "Jun", count: 20700 },
    { label: "Jul", count: 22400 },
    { label: "Ago", count: 23100 },
    { label: "Set", count: 26520 },
    { label: "Out", count: 28100 },
    { label: "Nov", count: 30200 },
    { label: "Dez", count: 32700 },
  ],
};

const metrics = [
  {
    label: "Faturamento mensal",
    value: "R$ 84.500",
    trend: "+12,4%",
    note: "em relação ao mês anterior",
  },
  {
    label: "Professores cadastrados",
    value: "36",
    trend: "+4",
    note: "novos professores neste mês",
  },
  {
    label: "Alunos cadastrados",
    value: "2.480",
    trend: "+8,7%",
    note: "crescimento no período",
  },
];

const numberFormatter = new Intl.NumberFormat("pt-BR");

export function AdminDashboard() {
  const [period, setPeriod] = useState<AccessPeriod>("monthly");
  const accesses = accessData[period];
  const totalAccesses = accesses.reduce((total, item) => total + item.count, 0);
  const maximum = Math.max(...accesses.map((item) => item.count));

  return (
    <AdminShell activePage="overview" topbarTitle="Performance do negócio">
      <div className={styles.dashboard}>
        <header className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>AprovaAí</span>
            <h1>Visão geral do negócio</h1>
            <p>Acompanhe os principais indicadores da plataforma.</p>
          </div>
          <span className={styles.demoBadge}>Dados ilustrativos</span>
        </header>

        <section className={styles.metrics} aria-label="Indicadores principais do negócio">
          {metrics.map((metric) => (
            <article className={styles.metricCard} key={metric.label}>
              <h2>{metric.label}</h2>
              <strong>{metric.value}</strong>
              <p><span>{metric.trend}</span> {metric.note}</p>
            </article>
          ))}
        </section>

        <section className={styles.chartCard} aria-labelledby="access-title">
          <div className={styles.chartHeader}>
            <div>
              <span className={styles.eyebrow}>Desempenho da plataforma</span>
              <h2 id="access-title">Acessos à plataforma</h2>
              <p>Compare a evolução de visitas no período mensal ou anual.</p>
            </div>
            <div className={styles.periodControls} role="group" aria-label="Período do gráfico">
              <button type="button" aria-pressed={period === "monthly"} onClick={() => setPeriod("monthly")}>
                Mensal
              </button>
              <button type="button" aria-pressed={period === "annual"} onClick={() => setPeriod("annual")}>
                Anual
              </button>
            </div>
          </div>

          <div className={styles.chartSummary} aria-live="polite">
            <strong>{numberFormatter.format(totalAccesses)}</strong>
            <span>acessos no período</span>
          </div>

          <div className={styles.chartViewport}>
            <ol
              className={styles.chartBars}
              style={{
                gridTemplateColumns: `repeat(${accesses.length}, minmax(54px, 1fr))`,
                minWidth: period === "annual" ? "760px" : "420px",
              }}
              aria-label={period === "monthly" ? "Acessos nas últimas quatro semanas" : "Acessos nos últimos doze meses"}
            >
              {accesses.map((item) => (
                <li className={styles.chartColumn} key={item.label}>
                  <span className={styles.barValue}>{numberFormatter.format(item.count)}</span>
                  <div className={styles.barTrack}>
                    <span className={styles.barFill} style={{ height: `${(item.count / maximum) * 100}%` }} />
                  </div>
                  <span className={styles.barLabel}>{item.label}</span>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className={styles.healthCard} aria-labelledby="health-title">
          <div>
            <span className={styles.eyebrow}>Saúde do negócio</span>
            <h2 id="health-title">Crescimento sustentável</h2>
            <p>Os acessos e o faturamento seguem em evolução positiva neste período.</p>
          </div>
          <dl className={styles.healthStats}>
            <div><dt>Conversão</dt><dd>6,8%</dd></div>
            <div><dt>Receita por aluno</dt><dd>R$ 34,07</dd></div>
            <div><dt>Retenção mensal</dt><dd>91,2%</dd></div>
          </dl>
        </section>
      </div>
    </AdminShell>
  );
}
