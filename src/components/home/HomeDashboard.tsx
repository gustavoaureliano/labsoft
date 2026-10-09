import { CatalogCourseCard } from "@/components/catalog/CatalogCourseCard";
import { PrimaryLink } from "@/components/ui/PrimaryLink";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { catalogCourses } from "@/data/catalog";
import { currentLesson, enrolledCourse, lessonHref } from "@/data/courses";
import Link from "next/link";
import styles from "./HomeDashboard.module.css";

export function HomeDashboard() {
  const currentLessonIndex = enrolledCourse.lessons.findIndex((lesson) => lesson.number === currentLesson.number);
  const previousLesson = enrolledCourse.lessons[currentLessonIndex - 1];
  const nextLesson = enrolledCourse.lessons[currentLessonIndex + 1];

  return (
    <div className={styles.dashboard}>
      <section className={styles.welcomeRow}>
        <div>
          <p className={styles.welcomeDate}>Sua área de estudos</p>
          <h1>Pronto para avançar hoje?</h1>
          <p>Continue sua aula, descubra novos cursos e organize sua revisão.</p>
        </div>
      </section>

      <section className={styles.continueSection} aria-labelledby="continue-title">
        <div className={styles.sectionHeading}>
          <div><span className={styles.eyebrow}>Continue de onde parou</span><h2 id="continue-title">Sua próxima aula está esperando</h2></div>
          <Link href="/meus-cursos">Ver meus cursos</Link>
        </div>

        <div className={styles.learningGrid}>
          <article className={styles.featuredCourse}>
            <div className={styles.featuredVisual} aria-hidden="true">
              <span>{enrolledCourse.category}</span>
              <strong>{currentLesson.number}</strong>
              <small>Aula atual</small>
            </div>
            <div className={styles.featuredContent}>
              <span className={styles.eyebrow}>{enrolledCourse.category} · Aula {currentLesson.number}</span>
              <h2>{currentLesson.title}</h2>
              <p>{enrolledCourse.title}</p>
              <p className={styles.teacherLine}><span className={styles.miniAvatar}>{enrolledCourse.teacherInitials}</span>{enrolledCourse.teacher}</p>
              <div className={styles.progressCopy}><span>Progresso do curso</span><strong>{enrolledCourse.progress}%</strong></div>
              <ProgressBar value={enrolledCourse.progress} />
              <PrimaryLink className={styles.primaryButton} href={lessonHref(currentLesson.id)}>Continuar assistindo</PrimaryLink>
            </div>
          </article>

          <aside className={styles.lessonRail} aria-label="Outras aulas do curso">
            <span className={styles.eyebrow}>Sua trilha</span>
            <h3>No seu curso</h3>
            {previousLesson && <Link className={styles.railLesson} href={lessonHref(previousLesson.id)}><span>Última aula · concluída</span><strong>{previousLesson.title}</strong></Link>}
            {nextLesson && <Link className={styles.railLesson} href={lessonHref(nextLesson.id)}><span>Depois desta</span><strong>{nextLesson.title}</strong></Link>}
            <Link className={styles.allLessonsLink} href={`/meus-cursos/${enrolledCourse.id}`}>Ver aulas do curso →</Link>
          </aside>
        </div>
      </section>

      <section id="meus-cursos" aria-labelledby="recommended-title">
        <div className={`${styles.sectionHeading} ${styles.sectionHeadingCompact}`}>
          <div><span className={styles.eyebrow}>Descubra algo novo</span><h2 id="recommended-title">Recomendados para você</h2></div>
          <Link href="/explorar-cursos">Explorar todos</Link>
        </div>
        <div className={styles.courseGrid}>{catalogCourses.map((course) => <CatalogCourseCard course={course} key={course.id} />)}</div>
      </section>

      <section className={styles.studySection} aria-labelledby="study-title">
        <div className={styles.sectionHeading}>
          <div><span className={styles.eyebrow}>Além das videoaulas</span><h2 id="study-title">Outras formas de estudar</h2></div>
        </div>
        <div className={styles.studyGrid}>
          <Link className={styles.studyCard} href="/materiais-complementares"><strong>Revise com materiais</strong><span>Encontre resumos e exercícios para reforçar o que aprendeu.</span><small>Ver materiais →</small></Link>
          <Link className={styles.studyCard} href="/duvidas"><strong>Tire uma dúvida</strong><span>Envie sua pergunta ao professor e acompanhe a resposta.</span><small>Ir para dúvidas →</small></Link>
        </div>
      </section>
    </div>
  );
}
