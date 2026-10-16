import Link from "next/link";
import { lessonHref, type EnrolledLesson } from "@/data/courses";
import styles from "./CourseLessonList.module.css";

type CourseLessonListProps = {
  lessons: EnrolledLesson[];
  activeLessonId?: string;
  compact?: boolean;
  getLessonHref?: (lesson: EnrolledLesson) => string;
  onRemoveLesson?: (lessonId: string) => void;
};

export function CourseLessonList({ lessons, activeLessonId, compact = false, getLessonHref = (lesson) => lessonHref(lesson.id), onRemoveLesson }: CourseLessonListProps) {
  return (
    <ol className={`${styles.list} ${compact ? styles.compact : ""}`}>
      {lessons.map((lesson) => (
        <li className={lesson.id === activeLessonId ? styles.active : ""} key={lesson.id}>
          <Link href={getLessonHref(lesson)} aria-current={lesson.id === activeLessonId ? "page" : undefined}>
            <span className={styles.number}>{lesson.number}</span>
            <span className={styles.copy}><strong>{lesson.title}</strong><small>{lesson.duration} · {lesson.status}</small></span>
            {!compact && <span className={styles.action}>{lesson.id === activeLessonId ? "Assistindo" : "Assistir"}</span>}
          </Link>
          {onRemoveLesson && <button className={styles.remove} type="button" onClick={() => onRemoveLesson(lesson.id)} aria-label={`Remover ${lesson.title} da playlist`}>Remover</button>}
        </li>
      ))}
    </ol>
  );
}
