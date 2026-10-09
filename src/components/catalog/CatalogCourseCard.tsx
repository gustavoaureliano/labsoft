import Image from "next/image";
import Link from "next/link";
import type { CatalogCourse } from "@/data/catalog";
import styles from "./CatalogCourseCard.module.css";

export function CatalogCourseCard({ course }: { course: CatalogCourse }) {
  return (
    <article className={styles.card}>
      <Link className={styles.link} href={`/cursos/${course.id}`} aria-label={`Ver detalhes de ${course.title}`}>
        <div className={styles.cover} data-group={course.group}>
          <Image alt={`Capa do curso ${course.title}`} fill sizes="(max-width: 700px) 100vw, 33vw" src={course.image} />
          <span className={styles.coverSubject}>{course.subject}</span>
        </div>
        <div className={styles.body}>
          <h3>{course.title}</h3>
          <p className={styles.teacher}>{course.teacher}</p>
          <p className={styles.details}>{course.lessonCount} aulas · {course.duration} · {course.exams.join(" e ")}</p>
          <div className={styles.cardFooter}>
            <span className={styles.rating} aria-label={`Avaliação ${course.rating} de 5`}>★ {course.rating.toFixed(1).replace(".", ",")}</span>
            <span className={styles.details}>{course.access === "free" ? "Gratuito" : "Ver curso"}</span>
          </div>
        </div>
      </Link>
    </article>
  );
}
