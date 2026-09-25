import type { Course } from "@/data/courses";
import styles from "./CourseCard.module.css";

export function CourseCard({ course }: { course: Course }) {
  return (
    <article className={styles.card}>
      <div className={styles.placeholder}>{course.category}</div>
      <div className={styles.body}>
        <span className={styles.category}>{course.category}</span>
        <h3>{course.title}</h3>
        <p>{course.teacher}</p>
        <div className={styles.meta}><span>Nota 4,8</span><span>{course.duration}</span></div>
      </div>
    </article>
  );
}
