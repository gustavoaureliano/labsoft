"use client";

import Link from "next/link";
import { CourseLessonList } from "@/components/learning/CourseLessonList";
import { LessonLibraryActions } from "@/components/learning/LessonLibraryActions";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { enrolledCourse, findEnrolledLesson, lessonHref, lessonsFromIds, type LessonCollectionContext } from "@/data/courses";
import { initialStudyDemo, studyDemoKey } from "@/data/studyDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { DemoPlayer } from "./DemoPlayer";
import { LessonTabs } from "./LessonTabs";
import styles from "./page.module.css";

type VideoLessonExperienceProps = {
  lessonId?: string;
  origin?: string;
  playlistId?: string;
};

type LessonCollection = {
  title: string;
  eyebrow: string;
  lessons: typeof enrolledCourse.lessons;
  context: LessonCollectionContext;
  backHref: string;
  backLabel: string;
};

export function VideoLessonExperience({ lessonId, origin, playlistId }: VideoLessonExperienceProps) {
  const [study, saveStudy, ready] = useDemoStorage(studyDemoKey, initialStudyDemo);
  const lesson = findEnrolledLesson(lessonId);
  const courseCollection: LessonCollection = {
    title: "Aulas do curso",
    eyebrow: enrolledCourse.title,
    lessons: enrolledCourse.lessons,
    context: { origin: "course" },
    backHref: `/meus-cursos/${enrolledCourse.id}`,
    backLabel: "Voltar para o curso",
  };

  let collection = courseCollection;
  if (ready && origin === "playlist" && playlistId) {
    const playlist = study.playlists.find((item) => item.id === playlistId);
    const playlistLessons = lessonsFromIds(playlist?.lessonIds ?? []);
    if (playlist && playlistLessons.some((item) => item.id === lesson.id)) {
      collection = {
        title: playlist.name,
        eyebrow: "Playlist de estudo",
        lessons: playlistLessons,
        context: { origin: "playlist", playlistId },
        backHref: `/meus-cursos/playlists/${playlistId}`,
        backLabel: "Voltar para a playlist",
      };
    }
  } else if (ready && (origin === "history" || origin === "favorites")) {
    const collectionLessons = lessonsFromIds(origin === "history" ? study.viewedLessons : study.favoriteLessons);
    if (collectionLessons.some((item) => item.id === lesson.id)) {
      collection = {
        title: origin === "history" ? "Histórico" : "Favoritos",
        eyebrow: "Biblioteca de estudo",
        lessons: collectionLessons,
        context: { origin },
        backHref: "/meus-cursos",
        backLabel: "Voltar para Meus Cursos",
      };
    }
  }

  const lessonIndex = collection.lessons.findIndex((item) => item.id === lesson.id);
  const previousLesson = collection.lessons[lessonIndex - 1];
  const nextLesson = collection.lessons[lessonIndex + 1];
  const collectionHref = (id: string) => lessonHref(id, collection.context);

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumbs}><Link className={styles.backLink} href={collection.backHref}>← {collection.backLabel}</Link><Link href="/meus-cursos">Meus Cursos</Link></div>
      <header className={styles.heading}>
        <span className={styles.eyebrow}><Link className={styles.courseLink} href={`/meus-cursos/${enrolledCourse.id}`}>{enrolledCourse.title}</Link> · Aula {lesson.number}</span>
        <h1>{lesson.title}</h1>
        <p>{enrolledCourse.teacher}</p>
      </header>

      <div className={styles.layout}>
        <section aria-label="Videoaula" className={styles.mainColumn}>
          <DemoPlayer lessonId={lesson.id} thumbnail={lesson.thumbnail ?? enrolledCourse.image} />
          <nav className={styles.lessonNavigation} aria-label="Navegar entre aulas"><span>{previousLesson ? <Link href={collectionHref(previousLesson.id)}>← Aula anterior</Link> : "Início da lista"}</span><span>{nextLesson ? <Link href={collectionHref(nextLesson.id)}>Próxima aula →</Link> : "Fim da lista"}</span></nav>
          <LessonLibraryActions lessonId={lesson.id} study={study} saveStudy={saveStudy} ready={ready} />
          <LessonTabs key={lesson.id} description={lesson.description} lessonId={lesson.id} lessonTitle={lesson.title} />
        </section>

        <aside className={styles.lessonPanel} aria-labelledby="lessons-title">
          <div className={styles.panelHeading}>
            <span className={styles.eyebrow}>{collection.eyebrow}</span>
            <h2 id="lessons-title">{collection.title}</h2>
            {collection.context.origin === "course" ? <><p>Seu progresso: {enrolledCourse.progress}%</p><div className={styles.progressBar}><ProgressBar value={enrolledCourse.progress} /></div></> : <p>{collection.lessons.length} {collection.lessons.length === 1 ? "aula nesta lista" : "aulas nesta lista"}</p>}
          </div>
          <CourseLessonList compact lessons={collection.lessons} activeLessonId={lesson.id} getLessonHref={(item) => collectionHref(item.id)} />
          <Link className={styles.allLessonsLink} href={collection.backHref}>{collection.context.origin === "course" ? "Ver página do curso" : collection.backLabel}</Link>
        </aside>
      </div>
    </div>
  );
}
