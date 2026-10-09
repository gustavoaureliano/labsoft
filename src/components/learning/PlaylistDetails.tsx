"use client";

import Link from "next/link";
import { lessonHref, lessonsFromIds } from "@/data/courses";
import { initialStudyDemo, studyDemoKey } from "@/data/studyDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { CourseLessonList } from "./CourseLessonList";
import styles from "./PlaylistDetails.module.css";

export function PlaylistDetails({ playlistId }: { playlistId: string }) {
  const [study, saveStudy, ready] = useDemoStorage(studyDemoKey, initialStudyDemo);
  const playlist = study.playlists.find((item) => item.id === playlistId);

  if (!ready) return <p className={styles.status}>Carregando playlist...</p>;
  if (!playlist) return <section className={styles.empty}><h1>Playlist não encontrada</h1><p>Ela pode ter sido removida deste navegador.</p><Link href="/meus-cursos">Voltar para Meus Cursos</Link></section>;

  const lessons = lessonsFromIds(playlist.lessonIds);

  function removeLesson(lessonId: string) {
    saveStudy({
      ...study,
      playlists: study.playlists.map((item) => item.id === playlistId ? { ...item, lessonIds: item.lessonIds.filter((id) => id !== lessonId) } : item),
    });
  }

  return (
    <div className={styles.page}>
      <Link className={styles.back} href="/meus-cursos">← Voltar para Meus Cursos</Link>
      <header className={styles.heading}>
        <span>Playlist de estudo</span>
        <h1>{playlist.name}</h1>
        <p>{lessons.length} {lessons.length === 1 ? "aula adicionada" : "aulas adicionadas"}. Escolha uma aula para continuar estudando.</p>
      </header>
      <section className={styles.content} aria-labelledby="playlist-lessons-title">
        <h2 id="playlist-lessons-title">Aulas da playlist</h2>
        {lessons.length > 0 ? (
          <CourseLessonList
            lessons={lessons}
            getLessonHref={(lesson) => lessonHref(lesson.id, { origin: "playlist", playlistId })}
            onRemoveLesson={removeLesson}
          />
        ) : <p className={styles.status}>Esta playlist ainda não tem aulas. Adicione uma pela página de uma videoaula.</p>}
      </section>
      <p className={styles.note}>Esta playlist fica somente neste navegador.</p>
    </div>
  );
}
