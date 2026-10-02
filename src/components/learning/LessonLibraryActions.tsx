"use client";

import { useEffect, useState } from "react";
import { initialStudyDemo, lessonDemoId, studyDemoKey } from "@/data/studyDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./LessonLibraryActions.module.css";

export function LessonLibraryActions() {
  const [study, saveStudy, ready] = useDemoStorage(studyDemoKey, initialStudyDemo);
  const [notice, setNotice] = useState("");
  const favorite = study.favoriteLessons.includes(lessonDemoId);

  useEffect(() => {
    if (!ready || study.viewedLessons.includes(lessonDemoId)) return;
    saveStudy({ ...study, viewedLessons: [...study.viewedLessons, lessonDemoId] });
  }, [ready, study, saveStudy]);

  function toggleFavorite() {
    saveStudy({ ...study, favoriteLessons: favorite ? study.favoriteLessons.filter((id) => id !== lessonDemoId) : [...study.favoriteLessons, lessonDemoId] });
    setNotice(favorite ? "Aula removida dos favoritos." : "Aula adicionada aos favoritos deste navegador.");
  }

  function addToPlaylist(playlistId: string) {
    if (!playlistId) return;
    saveStudy({ ...study, playlists: study.playlists.map((playlist) => playlist.id === playlistId && !playlist.lessonIds.includes(lessonDemoId) ? { ...playlist, lessonIds: [...playlist.lessonIds, lessonDemoId] } : playlist) });
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
