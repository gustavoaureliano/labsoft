import Link from "next/link";
import type { CatalogCourse } from "@/data/catalog";
import { formatPrice } from "@/data/catalog";
import { enrolledCourse } from "@/data/courses";
import styles from "./Commerce.module.css";

export function CourseDetails({ course }: { course: CatalogCourse }) {
  const isEnrolled = course.id === enrolledCourse.id;
  const actionHref = isEnrolled ? `/meus-cursos/${course.id}` : course.access === "free" ? `/checkout?curso=${course.id}&tipo=curso` : `/planos?curso=${course.id}`;

  return (
    <div className={styles.page}>
      <Link className={styles.back} href="/explorar-cursos">← Voltar para cursos</Link>
      <section className={styles.hero}>
        <div className={styles.heroMain}>
          <span className={styles.eyebrow}>{course.subject} · {course.exams.join(" e ")}</span>
          <h1>{course.title}</h1>
          <p className={styles.lead}>{course.summary}</p>
          <div className={styles.meta}><span>{course.lessonCount} aulas</span><span>{course.duration}</span><span>★ {course.rating.toFixed(1).replace(".", ",")}</span></div>
        </div>
        <aside className={styles.purchase} aria-label="Opções de acesso">
          <span className={styles.eyebrow}>{isEnrolled ? "Curso em andamento" : course.access === "free" ? "Acesso gratuito" : "Acesso ao curso"}</span>
          <strong>{isEnrolled ? `${enrolledCourse.progress}% concluído` : course.access === "free" ? "Gratuito" : formatPrice(course.price)}</strong>
          <p>{isEnrolled ? "Continue de onde parou na sua área de estudos." : course.access === "free" ? "Adicione este curso à sua área de estudos." : "Compre somente este curso ou escolha a assinatura completa."}</p>
          <Link className={styles.primary} href={actionHref}>{isEnrolled ? "Continuar curso" : course.access === "free" ? "Adicionar aos meus cursos" : "Escolher acesso"}</Link>
        </aside>
      </section>

      <div className={styles.detailsGrid}>
        <section className={styles.section} aria-labelledby="syllabus-title">
          <h2 id="syllabus-title">Ementa do curso</h2>
          <div className={styles.modules}>{course.syllabus.map((module) => <div className={styles.module} key={module.title}><h3>{module.title}</h3><ul>{module.lessons.map((lesson) => <li key={lesson}>{lesson}</li>)}</ul></div>)}</div>
        </section>
        <div className={styles.page}>
          <section className={styles.section}><h2>Para quem é</h2><p>{course.audience}</p></section>
          <section className={styles.section}><h2>Professor</h2><p><strong>{course.teacher}</strong></p><p>Conteúdo organizado para uma preparação objetiva e progressiva.</p></section>
        </div>
      </div>
    </div>
  );
}
