import { CourseCard } from "@/components/home/CourseCard";
import { recommendedCourses } from "@/data/courses";
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
          <a href="#meus-cursos">Ver meus cursos</a>
        </div>

        <article className={styles.featuredCourse}>
          <div className={styles.featuredVisual}>
            <span>Aula de Física</span>
          </div>
          <div className={styles.featuredContent}>
            <span className={styles.eyebrow}>Física · Aula 08</span>
            <h2>Leis de Newton e suas aplicações</h2>
            <p>Física para o ENEM: Mecânica</p>
            <p className={styles.teacherLine}><span className={styles.miniAvatar}>MA</span>Prof. Marcelo Andrade</p>
            <div className={styles.progressCopy}><span>Progresso do curso</span><strong>68%</strong></div>
            <div className={styles.progressBar} aria-label="68% concluído"><span style={{ width: "68%" }} /></div>
            <button className={styles.primaryButton} type="button">Continuar assistindo</button>
          </div>
        </article>
      </section>

      <section id="meus-cursos" aria-labelledby="recommended-title">
        <div className={`${styles.sectionHeading} ${styles.sectionHeadingCompact}`}>
          <div><span className={styles.eyebrow}>Descubra algo novo</span><h2 id="recommended-title">Recomendados para você</h2></div>
          <a href="#explorar">Explorar todos</a>
        </div>
        <div className={styles.courseGrid}>{recommendedCourses.map((course) => <CourseCard course={course} key={course.title} />)}</div>
      </section>
    </div>
  );
}
