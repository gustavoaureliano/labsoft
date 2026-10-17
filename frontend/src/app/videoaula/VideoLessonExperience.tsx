"use client";

import Link from "next/link";
import { CourseLessonList } from "@/components/learning/CourseLessonList";
import { LessonLibraryActions } from "@/components/learning/LessonLibraryActions";
import { VideoPlayer } from "@/components/learning/VideoPlayer";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { initialStudyDemo, studyDemoKey } from "@/data/studyDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { useApi, displayLessons, lessonLink, type Playback, type Course, type Dashboard } from "@/lib/api/learning";
import { LessonTabs } from "./LessonTabs";
import styles from "./page.module.css";

export function VideoLessonExperience({lessonId, origin, playlistId}: {lessonId?: string; origin?: string; playlistId?: string}) {
  const home = useApi<Dashboard>(lessonId ? null : "/api/learning/dashboard");
  const selected = lessonId ?? home.data?.current_course?.continue_lesson?.id;
  const playback = useApi<Playback>(selected ? `/api/learning/lessons/${encodeURIComponent(selected)}/playback` : null);
  const course = useApi<Course>(playback.data ? `/api/learning/courses/${playback.data.course_id}` : null);
  const [study, saveStudy, ready] = useDemoStorage(studyDemoKey, initialStudyDemo);
  const error = home.error || playback.error || course.error;
  if (error) return <div role="alert"><h1>Aula indisponível</h1><p>{error}</p><Link href="/meus-cursos">Voltar para Meus Cursos</Link></div>;
  if (!selected && home.data) return <p>Nenhuma aula disponível. <Link href="/meus-cursos">Ver cursos</Link></p>;
  if (!playback.data || !course.data) return <p role="status">Carregando aula...</p>;
  const lesson = playback.data;
  const info = course.data;
  const list = info.lessons;
  const index = list.findIndex(item => item.id === lesson.id);
  return <div className={styles.page}>
    <div className={styles.breadcrumbs}><Link href={`/meus-cursos/${info.id}`}>← Voltar para o curso</Link><Link href="/meus-cursos">Meus Cursos</Link></div>
    <header className={styles.heading}><span className={styles.eyebrow}><Link className={styles.courseLink} href={`/meus-cursos/${info.id}`}>{info.title}</Link> · Aula {lesson.position}</span><h1>{lesson.title}</h1><p>{info.teacher}</p></header>
    <div className={styles.layout}>
      <section className={styles.mainColumn} aria-label="Videoaula">
        <VideoPlayer key={`${lesson.id}:${lesson.media_id}`} lesson={lesson} poster={list.find(item => item.id === lesson.id)?.thumbnail_url ?? info.image} />
        <nav className={styles.lessonNavigation} aria-label="Navegar entre aulas"><span>{list[index - 1] && <Link href={lessonLink(list[index - 1].id, {origin, playlistId})}>← Aula anterior</Link>}</span><span>{list[index + 1] && <Link href={lessonLink(list[index + 1].id, {origin, playlistId})}>Próxima aula →</Link>}</span></nav>
        <LessonLibraryActions lessonId={lesson.id} study={study} saveStudy={saveStudy} ready={ready} />
        <LessonTabs key={lesson.id} description={lesson.description} lessonId={lesson.id} lessonTitle={lesson.title} />
      </section>
      <aside className={styles.lessonPanel}><div className={styles.panelHeading}><h2>Aulas do curso</h2><p>Seu progresso: {info.progress}%</p><ProgressBar value={info.progress} /></div><CourseLessonList compact lessons={displayLessons(list, lesson.id)} activeLessonId={lesson.id} getLessonHref={item => lessonLink(item.id)} /><Link className={styles.allLessonsLink} href={`/meus-cursos/${info.id}`}>Ver página do curso</Link></aside>
    </div>
  </div>;
}
