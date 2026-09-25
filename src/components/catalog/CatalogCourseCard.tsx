import Link from "next/link";
import type { CatalogCourse } from "@/data/catalog";
import styles from "./CatalogCourseCard.module.css";

export function CatalogCourseCard({ course }: { course: CatalogCourse }) {
  const coverMark = course.subject === "Física" ? "φ" : course.subject === "Biologia" ? "BIO" : course.subject === "Matemática" ? "∑" : course.subject === "Redação" ? "Aa" : course.subject === "Química" ? "H₂O" : "BR";

  return (
    <article className={styles.card}>
      <div className={styles.cover} data-group={course.group}>
        <span className={styles.coverMark} aria-hidden="true">{coverMark}</span>
        <span className={styles.coverSubject}>{course.subject}</span>
      </div>
      <div className={styles.body}>
        <h3>{course.title}</h3>
        <p className={styles.teacher}>{course.teacher}</p>
        <p className={styles.details}>{course.lessonCount} aulas · {course.duration} · {course.exams.join(" e ")}</p>
        <div className={styles.cardFooter}>
          <span className={styles.rating} aria-label={`Avaliação ${course.rating} de 5`}>★ {course.rating.toFixed(1).replace(".", ",")}</span>
          <Link className={styles.detailsLink} href="/videoaula">Ver detalhes</Link>
        </div>
      </div>
    </article>
  );
}