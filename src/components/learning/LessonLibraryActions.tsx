"use client";

import { useEffect, useRef, useState } from "react";
import type { StudyDemo } from "@/data/studyDemo";
import styles from "./LessonLibraryActions.module.css";

type LessonLibraryActionsProps = {
  lessonId: string;
  study: StudyDemo;
  saveStudy: (study: StudyDemo) => boolean;
  ready: boolean;
};

export function LessonLibraryActions({ lessonId, study, saveStudy, ready }: LessonLibraryActionsProps) {
  const [notice, setNotice] = useState("");
  const recordedLesson = useRef<string | null>(null);
  const favorite = study.favoriteLessons.includes(lessonId);

  useEffect(() => {
    if (!ready || recordedLesson.current === lessonId) return;
    recordedLesson.current = lessonId;
    saveStudy({ ...study, viewedLessons: [lessonId, ...study.viewedLessons.filter((id) => id !== lessonId)] });
  }, [ready, study, saveStudy, lessonId]);

  function toggleFavorite() {
    saveStudy({ ...study, favoriteLessons: favorite ? study.favoriteLessons.filter((id) => id !== lessonId) : [...study.favoriteLessons, lessonId] });
    setNotice(favorite ? "Aula removida dos favoritos." : "Aula adicionada aos favoritos deste navegador.");
  }

  function addToPlaylist(playlistId: string) {
    if (!playlistId) return;
    saveStudy({ ...study, playlists: study.playlists.map((playlist) => playlist.id === playlistId && !playlist.lessonIds.includes(lessonId) ? { ...playlist, lessonIds: [...playlist.lessonIds, lessonId] } : playlist) });
    setNotice("Aula adicionada à playlist neste navegador.");
  }

  return (
    <div className={styles.actions}>
      <button type="button" aria-pressed={favorite} onClick={toggleFavorite}>{favorite ? "★ Salvo nos favoritos" : "☆ Salvar nos favoritos"}</button>
      <label>Adicionar à playlist <select value="" onChange={(event) => addToPlaylist(event.target.value)}><option value="">Escolha uma playlist</option>{study.playlists.map((playlist) => <option key={playlist.id} value={playlist.id}>{playlist.name}</option>)}</select></label>
      {notice && <p role="status">{notice}</p>}
    </div>
  );
}
