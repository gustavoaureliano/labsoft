import { CourseCard } from "@/components/home/CourseCard";
import { PrimaryLink } from "@/components/ui/PrimaryLink";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { currentLesson, enrolledCourse, recommendedCourses } from "@/data/courses";
import Link from "next/link";
import styles from "./HomeDashboard.module.css";

export function HomeDashboard() {
  return (
    <div className={styles.dashboard}>
      <section className={styles.welcomeRow}>
        <div>
          <p className={styles.welcomeDate}>Quarta-feira, 24 de setembro</p>
          <h1>Olá, Fulano!</h1>
          <p>Pronto para continuar aprendendo?</p>
        </div>
      </section>

      <section className={styles.continueSection} aria-labelledby="continue-title">
        <div className={styles.sectionHeading}>
          <div><span className={styles.eyebrow}>Continue de onde parou</span><h2 id="continue-title">Sua próxima aula está esperando</h2></div>
          <Link href="/meus-cursos">Ver meus cursos</Link>
        </div>

        <article className={styles.featuredCourse}>
          <div className={styles.featuredVisual}>
            <span>Aula de {enrolledCourse.category}</span>
          </div>
          <div className={styles.featuredContent}>
            <span className={styles.eyebrow}>{enrolledCourse.category} · Aula {currentLesson.number}</span>
            <h2>{currentLesson.title}</h2>
            <p>{enrolledCourse.title}</p>
            <p className={styles.teacherLine}><span className={styles.miniAvatar}>{enrolledCourse.teacherInitials}</span>{enrolledCourse.teacher}</p>
            <div className={styles.progressCopy}><span>Progresso do curso</span><strong>{enrolledCourse.progress}%</strong></div>
            <ProgressBar value={enrolledCourse.progress} />
            <PrimaryLink className={styles.primaryButton} href="/videoaula">Continuar assistindo</PrimaryLink>
          </div>
        </article>
      </section>

      <section id="meus-cursos" aria-labelledby="recommended-title">
        <div className={`${styles.sectionHeading} ${styles.sectionHeadingCompact}`}>
          <div><span className={styles.eyebrow}>Descubra algo novo</span><h2 id="recommended-title">Recomendados para você</h2></div>
          <Link href="/explorar-cursos">Explorar todos</Link>
        </div>
        <div className={styles.courseGrid}>{recommendedCourses.map((course) => <CourseCard course={course} key={course.title} />)}</div>
      </section>
    </div>
  );
}
