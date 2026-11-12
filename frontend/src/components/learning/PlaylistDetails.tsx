"use client";

import { useState } from "react";
import Link from "next/link";
import { useApi, displayLessons, lessonLink, type Course } from "@/lib/api/learning";
import { resolveLessons, useLibrary } from "@/lib/api/library";
import { isApiConfigured } from "@/lib/apiClient";
import { CourseLessonList } from "./CourseLessonList";
import styles from "./PlaylistDetails.module.css";

export function PlaylistDetails({ playlistId }: { playlistId: string }) {
  const {data: courses, error} = useApi<Course[]>("/api/learning/courses");
  const {study, saveStudy, ready, error: libraryError, updatePlaylistLessons} = useLibrary();
  const playlist = study.playlists.find((item) => item.id === playlistId);
  const [actionError, setActionError] = useState("");

  if (error || libraryError) return <p role="alert">{error || libraryError}</p>;
  if (!ready || !courses) return <p className={styles.status}>Carregando playlist...</p>;
  if (!playlist) return <section className={styles.empty}><h1>Playlist não encontrada</h1><p>{isApiConfigured ? "Ela pode ter sido removida ou não pertence à sua conta." : "Ela pode ter sido removida deste navegador."}</p><Link href="/meus-cursos">Voltar para Meus Cursos</Link></section>;

  const resolved = resolveLessons(playlist.lessonIds, courses);
  const lessons = displayLessons(resolved);

  async function removeLesson(lessonId: string) {
    if (isApiConfigured && updatePlaylistLessons) {
      setActionError("");
      try { await updatePlaylistLessons(playlistId, playlist!.lessonIds.filter(id => id !== lessonId)); }
      catch (err) { setActionError(`Não foi possível remover a aula da playlist: ${err instanceof Error ? err.message : "erro desconhecido"}`); }
      return;
    }
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
      {actionError && <p role="alert">{actionError}</p>}
      <section className={styles.content} aria-labelledby="playlist-lessons-title">
        <h2 id="playlist-lessons-title">Aulas da playlist</h2>
        {lessons.length > 0 ? (
          <CourseLessonList
            lessons={lessons}
            getLessonHref={(lesson) => lessonLink(lesson.id, { origin: "playlist", playlistId })}
            onRemoveLesson={lessonId => { void removeLesson(lessonId); }}
          />
        ) : <p className={styles.status}>Esta playlist ainda não tem aulas. Adicione uma pela página de uma videoaula.</p>}
      </section>
      {resolved.length < playlist.lessonIds.length && <p role="status">Algumas referências antigas, removidas ou sem acesso não estão disponíveis. Os identificadores foram preservados, sem substituir suas aulas.</p>}
      {!isApiConfigured && <p className={styles.note}>Esta playlist fica somente neste navegador.</p>}
    </div>
  );
}
