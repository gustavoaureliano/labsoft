"use client";

import Link from "next/link";
import { lessonHref, lessonsFromIds } from "@/data/courses";
import { useStudyLibrary } from "@/lib/engagementApi";
import { CourseLessonList } from "./CourseLessonList";
import styles from "./PlaylistDetails.module.css";

export function PlaylistDetails({ playlistId }: { playlistId: string }) {
  const { study, ready, usingBackend, updatePlaylistLessons } = useStudyLibrary();
  const playlist = study.playlists.find((item) => item.id === playlistId);

  if (!ready) return <p className={styles.status}>Carregando playlist...</p>;
  if (!playlist) return <section className={styles.empty}><h1>Playlist não encontrada</h1><p>Ela pode ter sido removida.</p><Link href="/meus-cursos">Voltar para Meus Cursos</Link></section>;

  const lessons = lessonsFromIds(playlist.lessonIds);

  async function removeLesson(lessonId: string) {
    if (!playlist) return;
    const nextLessonIds = playlist.lessonIds.filter((id) => id !== lessonId);
    await updatePlaylistLessons(playlistId, nextLessonIds);
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
      <p className={styles.note}>{usingBackend ? "Playlist sincronizada com o banco de dados." : "Esta playlist fica somente neste navegador."}</p>
    </div>
  );
}
