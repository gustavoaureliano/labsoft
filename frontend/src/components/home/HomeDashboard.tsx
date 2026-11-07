"use client";

import { CatalogCourseCard } from "@/components/catalog/CatalogCourseCard";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { catalogCourses } from "@/data/catalog";
import { useApi, lessonLink, type Dashboard } from "@/lib/api/learning";
import Image from "next/image";
import Link from "next/link";
import styles from "./HomeDashboard.module.css";

export function HomeDashboard() {
  const {data, error} = useApi<Dashboard>("/api/learning/dashboard");
  if (error) return <section role="alert"><h1>Não foi possível carregar sua Home</h1><p>{error}</p><Link href="/meus-cursos">Ver meus cursos</Link></section>;
  if (!data) return <p role="status">Carregando sua área de estudos...</p>;
  const course = data.current_course;
  const lesson = course?.continue_lesson;
  const index = course?.lessons.findIndex(item => item.id === lesson?.id) ?? -1;
  const recommendations = data.recommendations.flatMap(item => {const card = catalogCourses.find(course => course.id === item.id); return card ? [card] : [];});
  return <div className={styles.dashboard}>
    <section className={styles.welcomeRow}><p className={styles.welcomeDate}>Sua área de estudos</p><h1>Pronto para avançar hoje?</h1><p>Continue sua aula, descubra novos cursos e organize sua revisão.</p></section>
    <section className={styles.continueSection} aria-labelledby="continue-title">
      <div className={styles.sectionHeading}><div><span className={styles.eyebrow}>Continue de onde parou</span><h2 id="continue-title">Sua próxima aula está esperando</h2></div><Link href="/meus-cursos">Ver meus cursos</Link></div>
      {course && lesson ? <div className={styles.learningGrid}>
        <Link className={styles.featuredCourse} href={lessonLink(lesson.id)} aria-label={`Continuar aula ${lesson.title}`}>
          <div className={styles.featuredVisual} aria-hidden="true"><Image unoptimized alt="" fill priority sizes="(max-width: 900px) 100vw, 40vw" src={lesson.thumbnail_url ?? course.image} /><strong>{String(lesson.position).padStart(2, "0")}</strong><small>Aula atual</small></div>
          <div className={styles.featuredContent}><span className={styles.eyebrow}>Aula {lesson.position}</span><h2>{lesson.title}</h2><p>{course.title}</p><p className={styles.teacherLine}>{course.teacher}</p><div className={styles.progressCopy}><span>Progresso do curso</span><strong>{course.progress}%</strong></div><ProgressBar value={course.progress} /><span className={styles.continueAction}>Continuar assistindo →</span></div>
        </Link>
        <aside className={styles.lessonRail} aria-label="Outras aulas do curso"><span className={styles.eyebrow}>Sua trilha</span><h3>No seu curso</h3>{[course.lessons[index - 1], course.lessons[index + 1]].filter(Boolean).map(item => <Link key={item.id} className={styles.railLesson} href={lessonLink(item.id)}><span>{item.completed ? "Concluída" : "No seu curso"}</span><strong>{item.title}</strong></Link>)}<Link className={styles.allLessonsLink} href={`/meus-cursos/${course.id}`}>Ver aulas do curso →</Link></aside>
      </div> : <p>Você ainda não tem uma aula disponível para continuar. <Link href="/meus-cursos">Ver cursos</Link></p>}
    </section>
    <section id="meus-cursos" aria-labelledby="recommended-title"><div className={styles.sectionHeading}><div><span className={styles.eyebrow}>Descubra algo novo</span><h2 id="recommended-title">Recomendados para você</h2></div><Link href="/explorar-cursos">Explorar todos</Link></div><div className={styles.courseGrid}>{recommendations.map(item => <CatalogCourseCard key={item.id} course={item} />)}</div>{recommendations.length === 0 && <p>Nenhuma recomendação disponível no momento.</p>}</section>
    <section className={styles.studySection} aria-labelledby="study-title"><h2 id="study-title">Outras formas de estudar</h2><div className={styles.studyGrid}><Link className={styles.studyCard} href="/materiais-complementares"><strong>Revise com materiais</strong><span>Encontre resumos e exercícios.</span><small>Ver materiais →</small></Link><Link className={styles.studyCard} href="/duvidas"><strong>Tire uma dúvida</strong><span>Envie sua pergunta ao professor.</span><small>Ir para dúvidas →</small></Link></div></section>
    {data.notifications.length > 0 && <section><h2>Avisos</h2>{data.notifications.map((item, index) => <p key={index}>{item.title ?? item.message}</p>)}</section>}
  </div>;
}
