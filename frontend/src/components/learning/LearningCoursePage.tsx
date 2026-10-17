"use client";

import Link from "next/link";
import { useApi, displayLessons, lessonLink, type Course } from "@/lib/api/learning";
import { CourseLessonList } from "./CourseLessonList";
import { ProgressBar } from "@/components/ui/ProgressBar";
import styles from "@/app/meus-cursos/[id]/page.module.css";

export function LearningCoursePage({id}: {id: string}) {
  const {data: course, error} = useApi<Course>(`/api/learning/courses/${encodeURIComponent(id)}`);
  if (error) return <section role="alert"><h1>Curso indisponível</h1><p>{error}</p><Link href="/meus-cursos">Voltar para Meus Cursos</Link></section>;
  if (!course) return <p role="status">Carregando curso...</p>;
  return <div className={styles.page}>
    <Link className={styles.back} href="/meus-cursos">← Voltar para Meus Cursos</Link>
    <header className={styles.hero}><div><h1>{course.title}</h1><p>{course.total_lessons} aulas</p><small>{course.teacher}</small></div><aside><div><span>Progresso do curso</span><strong>{course.progress}%</strong></div><ProgressBar value={course.progress} />{course.continue_lesson && <Link href={lessonLink(course.continue_lesson.id)}>Continuar na aula {course.continue_lesson.position}</Link>}<Link className={styles.secondaryAction} href={`/duvidas?curso=${encodeURIComponent(course.id)}`}>Tirar dúvida sobre este curso</Link></aside></header>
    <section className={styles.content} aria-labelledby="course-content-title"><div className={styles.heading}><h2 id="course-content-title">Conteúdo do curso</h2><p>Escolha uma aula para assistir ou revisar.</p></div>{course.sections.map(section => <section className={styles.module} key={section.title}><h3>{section.title}</h3><CourseLessonList lessons={displayLessons(course.lessons.filter(item => section.lesson_ids.includes(item.id)), course.continue_lesson?.id)} activeLessonId={course.continue_lesson?.id} getLessonHref={item => lessonLink(item.id)} /></section>)}{course.lessons.length === 0 && <p>Este curso ainda não possui aulas.</p>}</section>
  </div>;
}
