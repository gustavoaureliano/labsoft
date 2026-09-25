import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { currentLesson, enrolledCourse } from "@/data/courses";
import { DemoPlayer } from "./DemoPlayer";
import styles from "./page.module.css";

export default function VideoAula() {
  return (
    <AppShell activePage="courses">
      <div className={styles.page}>
        <Link className={styles.backLink} href="/meus-cursos">← Voltar para meus cursos</Link>
        <header className={styles.heading}>
          <span className={styles.eyebrow}>{enrolledCourse.title} · Aula {currentLesson.number}</span>
          <h1>{currentLesson.title}</h1>
          <p>{enrolledCourse.teacher}</p>
        </header>

        <div className={styles.layout}>
          <section aria-label="Videoaula" className={styles.mainColumn}>
            <DemoPlayer />
            <div className={styles.description}>
              <h2>Sobre esta aula</h2>
              <p>{currentLesson.description}</p>
            </div>
          </section>

          <aside className={styles.lessonPanel} aria-labelledby="lessons-title">
            <div className={styles.panelHeading}>
              <span className={styles.eyebrow}>{enrolledCourse.title}</span>
              <h2 id="lessons-title">Aulas do curso</h2>
              <p>Seu progresso: {enrolledCourse.progress}%</p>
              <div className={styles.progressBar}><ProgressBar value={enrolledCourse.progress} /></div>
            </div>
            <ol className={styles.lessonList}>
              {enrolledCourse.lessons.map((lesson) => (
                <li className={lesson.number === enrolledCourse.currentLessonNumber ? styles.currentLesson : ""} key={lesson.number}>
                  <span className={styles.lessonNumber}>{lesson.number}</span>
                  <span><strong>{lesson.title}</strong><small>{lesson.status}</small></span>
                </li>
              ))}
            </ol>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
