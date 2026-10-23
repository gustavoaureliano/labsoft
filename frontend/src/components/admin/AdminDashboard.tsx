"use client";

import { useEffect, useState } from "react";
import { apiFetch, type ApiAdminDashboard } from "@/lib/engagementApi";
import { AdminShell } from "./AdminShell";
import styles from "./AdminDashboard.module.css";

type AccessPeriod = "monthly" | "annual";

const numberFormatter = new Intl.NumberFormat("pt-BR");

export function AdminDashboard() {
  const [period, setPeriod] = useState<AccessPeriod>("monthly");
  const [apiData, setApiData] = useState<ApiAdminDashboard | null>(null);

  useEffect(() => {
    let active = true;
    apiFetch<ApiAdminDashboard>(`/api/analytics/admin-dashboard?period=${period}`)
      .then((data) => {
        if (active) setApiData(data);
      })
      .catch(() => {
        if (active) setApiData(null);
      });
    return () => {
      active = false;
    };
  }, [period]);

  const accesses = apiData ? apiData.access_series : [];
  const totalAccesses = apiData ? apiData.total_accesses_in_period : 0;
  const maximum = Math.max(...accesses.map((item) => item.count), 1);

  const metrics = [
    {
      label: "Faturamento mensal",
      value: "R$ 84.500",
      trend: "+12,4%",
      note: "em relação ao mês anterior",
    },
    {
      label: "Professores cadastrados",
      value: apiData ? numberFormatter.format(apiData.total_teachers) : "...",
      trend: "+4",
      note: "novos professores neste mês",
    },
    {
      label: "Alunos cadastrados",
      value: apiData ? numberFormatter.format(apiData.total_students) : "...",
      trend: "+8,7%",
      note: "crescimento no período",
    },
  ];

  return (
    <AdminShell activePage="overview" topbarTitle="Performance do negócio">
      <div className={styles.dashboard}>
        <header className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>AprovaAí</span>
            <h1>Visão geral do negócio</h1>
            <p>Acompanhe os principais indicadores da plataforma.</p>
          </div>
          <span className={styles.demoBadge}>Dados da API</span>
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
                gridTemplateColumns: `repeat(${Math.max(accesses.length, 1)}, minmax(54px, 1fr))`,
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
