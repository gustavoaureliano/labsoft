"use client";

import { useEffect, useRef, useState } from "react";
import type { StudyDemo } from "@/data/studyDemo";
import styles from "./LessonLibraryActions.module.css";

type LessonLibraryActionsProps = {
  lessonId: string;
  study: StudyDemo;
  saveStudy: (study: StudyDemo) => boolean;
  ready: boolean;
  onRecordView?: (lessonId: string) => Promise<void> | void;
  onToggleFavorite?: (lessonId: string) => Promise<boolean>;
  onUpdatePlaylistLessons?: (playlistId: string, lessonIds: string[]) => Promise<boolean>;
};

export function LessonLibraryActions({
  lessonId,
  study,
  ready,
  onRecordView,
  onToggleFavorite,
  onUpdatePlaylistLessons,
}: LessonLibraryActionsProps) {
  const [notice, setNotice] = useState("");
  const recordedLesson = useRef<string | null>(null);
  const favorite = study.favoriteLessons.includes(lessonId);

  useEffect(() => {
    if (!ready || recordedLesson.current === lessonId || !onRecordView) return;
    recordedLesson.current = lessonId;
    Promise.resolve(onRecordView(lessonId)).catch((err) => {
      setNotice(err instanceof Error ? `Erro ao registrar histórico: ${err.message}` : "Erro ao registrar histórico.");
    });
  }, [ready, lessonId, onRecordView]);

  async function toggleFavorite() {
    if (!onToggleFavorite) return;
    try {
      const nowFav = await onToggleFavorite(lessonId);
      setNotice(nowFav ? "Aula adicionada aos favoritos deste navegador." : "Aula removida dos favoritos.");
    } catch (err) {
      setNotice(err instanceof Error ? `Erro nos favoritos: ${err.message}` : "Erro ao atualizar favoritos.");
    }
  }

  async function addToPlaylist(playlistId: string) {
    if (!playlistId || !onUpdatePlaylistLessons) return;
    const target = study.playlists.find((p) => p.id === playlistId);
    if (!target) return;
    try {
      if (!target.lessonIds.includes(lessonId)) {
        const nextLessons = [...target.lessonIds, lessonId];
        await onUpdatePlaylistLessons(playlistId, nextLessons);
      }
      setNotice("Aula adicionada à playlist neste navegador.");
    } catch (err) {
      setNotice(err instanceof Error ? `Erro na playlist: ${err.message}` : "Erro ao atualizar playlist.");
    }
  }

  return (
    <div className={styles.actions}>
      <button type="button" aria-pressed={favorite} onClick={toggleFavorite}>{favorite ? "★ Salvo nos favoritos" : "☆ Salvar nos favoritos"}</button>
      <label>Adicionar à playlist <select value="" onChange={(event) => addToPlaylist(event.target.value)}><option value="">Escolha uma playlist</option>{study.playlists.map((playlist) => <option key={playlist.id} value={playlist.id}>{playlist.name}</option>)}</select></label>
      {notice && <p role="status">{notice}</p>}
    </div>
  );
}
