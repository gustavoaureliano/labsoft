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
import { resolveLessons } from "@/lib/api/library";
import styles from "./page.module.css";

export function VideoLessonExperience({lessonId, origin, playlistId}: {lessonId?: string; origin?: string; playlistId?: string}) {
  const home = useApi<Dashboard>(lessonId ? null : "/api/learning/dashboard");
  const selected = lessonId ?? home.data?.current_course?.continue_lesson?.id;
  const playback = useApi<Playback>(selected ? `/api/learning/lessons/${encodeURIComponent(selected)}/playback` : null);
  const course = useApi<Course>(playback.data ? `/api/learning/courses/${playback.data.course_id}` : null);
  const accessibleCourses = useApi<Course[]>(selected && playback.error ? "/api/learning/courses" : null);
  const [study, saveStudy, ready] = useDemoStorage(studyDemoKey, initialStudyDemo);
  const library = useApi<Course[]>(origin && origin !== "course" ? "/api/learning/courses" : null);
  const error = home.error || course.error || library.error || accessibleCourses.error;
  if (error) return <div role="alert"><h1>Aula indisponível</h1><p>{error}</p><Link href="/meus-cursos">Voltar para Meus Cursos</Link></div>;
  if (!selected && home.data) return <p>Nenhuma aula disponível. <Link href="/meus-cursos">Ver cursos</Link></p>;
  if (playback.error && accessibleCourses.data && !accessibleCourses.data.some(item => item.lessons.some(lesson => lesson.id === selected))) {
    return <div role="alert"><h1>Aula indisponível</h1><p>{playback.error}</p><Link href="/meus-cursos">Voltar para Meus Cursos</Link></div>;
  }
  if ((!playback.data && (!playback.error || !accessibleCourses.data)) ||
      (playback.data && !course.data) ||
      (origin && origin !== "course" && (!library.data || !ready))) return <p role="status">Carregando aula...</p>;
  const info = course.data ?? accessibleCourses.data?.find(item => item.lessons.some(lesson => lesson.id === selected));
  const lesson = playback.data ?? info?.lessons.find(item => item.id === selected);
  if (!lesson || !info) return <div role="alert"><h1>Aula indisponível</h1><Link href="/meus-cursos">Voltar para Meus Cursos</Link></div>;
  const playlist = origin === "playlist" ? study.playlists.find(item => item.id === playlistId) : null;
  const ids = origin === "playlist" ? playlist?.lessonIds : origin === "history" ? study.viewedLessons : origin === "favorites" ? study.favoriteLessons : null;
  const list = ids ? resolveLessons(ids, library.data ?? []) : info.lessons;
  if ((origin === "playlist" && !playlist) || (ids && !list.some(item => item.id === lesson.id))) return <p role="alert">Aula não disponível nesta coleção. <Link href="/meus-cursos">Voltar à biblioteca</Link></p>;
  const collectionTitle = playlist?.name ?? (origin === "history" ? "Histórico" : origin === "favorites" ? "Favoritos" : "Aulas do curso");
  const backHref = playlist ? `/meus-cursos/playlists/${playlist.id}` : ids ? "/meus-cursos" : `/meus-cursos/${info.id}`;
  const index = list.findIndex(item => item.id === lesson.id);
  return <div className={styles.page}>
    <div className={styles.breadcrumbs}><Link href={backHref}>{playlist ? "← Voltar para a playlist" : ids ? "← Voltar para a biblioteca" : "← Voltar para o curso"}</Link><Link href="/meus-cursos">Meus Cursos</Link></div>
    <header className={styles.heading}><span className={styles.eyebrow}><Link className={styles.courseLink} href={`/meus-cursos/${info.id}`}>{info.title}</Link> · Aula {lesson.position}</span><h1>{lesson.title}</h1><p>{info.teacher}</p></header>
    <div className={styles.layout}>
      <section className={styles.mainColumn} aria-label="Videoaula">
        {playback.data ? <VideoPlayer key={`${lesson.id}:${lesson.media_id}`} lesson={playback.data} poster={list.find(item => item.id === lesson.id)?.thumbnail_url ?? info.image} /> : <div className={styles.unavailablePlayer} role="alert"><strong>Vídeo indisponível nesta aula</strong><p>{playback.error}</p><span>Você ainda pode consultar a descrição ou escolher outra aula do curso.</span></div>}
        <nav className={styles.lessonNavigation} aria-label="Navegar entre aulas"><span>{list[index - 1] && <Link href={lessonLink(list[index - 1].id, {origin, playlistId})}>← Aula anterior</Link>}</span><span>{list[index + 1] && <Link href={lessonLink(list[index + 1].id, {origin, playlistId})}>Próxima aula →</Link>}</span></nav>
        <LessonLibraryActions lessonId={lesson.id} study={study} saveStudy={saveStudy} ready={ready} />
        <LessonTabs key={lesson.id} description={lesson.description} lessonId={lesson.id} lessonTitle={lesson.title} courseId={info.id} />
      </section>
      <aside className={styles.lessonPanel}><div className={styles.panelHeading}><h2>{collectionTitle}</h2>{ids ? <p>{list.length} aulas nesta lista</p> : <><p>Seu progresso: {info.progress}%</p><ProgressBar value={info.progress} /></>}</div><CourseLessonList compact lessons={displayLessons(list, lesson.id)} activeLessonId={lesson.id} getLessonHref={item => lessonLink(item.id, {origin, playlistId})} />{ids && list.length < ids.length && <p>Algumas aulas da lista estão indisponíveis; suas referências foram preservadas.</p>}<Link className={styles.allLessonsLink} href={backHref}>{ids ? "Ver biblioteca" : "Ver página do curso"}</Link></aside>
    </div>
  </div>;
}
