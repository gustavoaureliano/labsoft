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
  { title: "Introdução à Filosofia", students: 486, revenue: "R$ 4.860", share: "52,6%" },
  { title: "Ética e Sociedade", students: 271, revenue: "R$ 2.710", share: "29,3%" },
  { title: "Pensamento Contemporâneo", students: 167, revenue: "R$ 1.670", share: "18,1%" },
];

const maximumRevenue = Math.max(...revenue.map((item) => item.value));

export function TeacherMonetization() {
  return (
    <TeacherShell>
      <div className={styles.page}>
        <header className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>Relatórios do professor</span>
            <h1>Monetização e desempenho</h1>
            <p>Acompanhe receitas, pagamentos e o engajamento dos seus alunos.</p>
          </div>
          <span className={styles.period}>Últimos 30 dias</span>
        </header>

        <section className={styles.metrics} aria-label="Resumo financeiro">
          <article><span>Receita mensal</span><strong>R$ 9.240</strong><p><b>+10,8%</b> sobre o mês anterior</p></article>
          <article><span>Saldo disponível</span><strong>R$ 7.890</strong><p>Próximo repasse em 5 dias</p></article>
          <article><span>Alunos pagantes</span><strong>924</strong><p><b>+68</b> novas matrículas</p></article>
        </section>

        <div className={styles.reportGrid}>
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

          <section className={styles.card} aria-labelledby="engagement-title">
            <div className={styles.cardHeader}><div><span className={styles.eyebrow}>Engajamento</span><h2 id="engagement-title">Atividade dos alunos</h2></div></div>
            <dl className={styles.engagement}>
              <div><dt>Taxa de conclusão</dt><dd>78,4%</dd><small>+4,2 pontos no mês</small></div>
              <div><dt>Tempo médio assistido</dt><dd>42 min</dd><small>por aluno na semana</small></div>
              <div><dt>Avaliação média</dt><dd>4,8/5</dd><small>com 612 avaliações</small></div>
              <div><dt>Alunos ativos</dt><dd>81%</dd><small>nos últimos 7 dias</small></div>
            </dl>
          </section>
        </div>

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
