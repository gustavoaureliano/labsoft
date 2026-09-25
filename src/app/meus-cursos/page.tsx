import { AppShell } from "@/components/layout/AppShell";
import { PrimaryLink } from "@/components/ui/PrimaryLink";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { currentLesson, enrolledCourse } from "@/data/courses";
import styles from "./page.module.css";

export default function MeusCursos() {
  return (
    <AppShell activePage="courses">
      <div className={styles.page}>
        <header className={styles.heading}>
          <span className={styles.eyebrow}>Sua jornada de aprendizado</span>
          <h1>Meus cursos</h1>
          <p>Acompanhe seu progresso e continue de onde parou.</p>
        </header>

        <section aria-labelledby="in-progress-title">
          <h2 id="in-progress-title">Em andamento</h2>
          <article className={styles.course}>
            <div className={styles.courseVisual}>{enrolledCourse.category}</div>
            <div className={styles.courseContent}>
              <span className={styles.eyebrow}>{enrolledCourse.category} · {enrolledCourse.totalLessons} aulas</span>
              <h3>{enrolledCourse.title}</h3>
              <p>{enrolledCourse.teacher}</p>
              <div className={styles.progressCopy}><span>Progresso do curso</span><strong>{enrolledCourse.progress}%</strong></div>
              <ProgressBar value={enrolledCourse.progress} />
              <p className={styles.nextLesson}>Próxima aula: {currentLesson.title}</p>
              <PrimaryLink className={styles.primaryButton} href="/videoaula">Continuar curso</PrimaryLink>
            </div>
          </article>
        </section>
      </div>
    </AppShell>
  );
}
