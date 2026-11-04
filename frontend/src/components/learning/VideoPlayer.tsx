"use client";

import { useEffect, useRef, useState } from "react";
import { api, jsonRequest, type Playback } from "@/lib/api/learning";
import styles from "./VideoPlayer.module.css";

export function VideoPlayer({lesson, preview = false, poster}: {lesson: Playback; preview?: boolean; poster?: string}) {
  const video = useRef<HTMLVideoElement>(null);
  const [playbackError, setPlaybackError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saved, setSaved] = useState<number | null>(null);
  const pending = useRef<number | null>(null);
  const saving = useRef(false);
  const mounted = useRef(true);
  const lastSave = useRef(0);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; pending.current = null; };
  }, []);

  async function savePosition(force = false) {
    const element = video.current;
    if (preview || !element || !Number.isFinite(element.currentTime)) return;
    if (!force && Date.now() - lastSave.current < 5000) return;
    lastSave.current = Date.now();
    pending.current = Math.min(element.currentTime, lesson.duration_seconds ?? element.currentTime);
    if (saving.current) return;
    saving.current = true;
    try {
      while (pending.current !== null && mounted.current) {
        const position = pending.current;
        pending.current = null;
        await api(`/api/learning/lessons/${lesson.id}/progress`, jsonRequest("PATCH", {media_id: lesson.media_id, position_seconds: position}));
        if (mounted.current) { setSaved(position); setSaveError(""); }
      }
    } catch (error) {
      if (mounted.current) setSaveError(`Progresso não salvo: ${(error as Error).message}`);
    } finally { saving.current = false; }
  }

  return <div>
    {playbackError ? <div className={styles.unavailable} role="alert"><strong>Não foi possível reproduzir este vídeo</strong><p>{playbackError}</p><span>Você pode consultar a aula ou selecionar outra da lista.</span></div> : <video ref={video} controls preload="metadata" poster={poster} style={{width: "100%", aspectRatio: "16 / 9", background: "#10242d", borderRadius: 8}}
      src={lesson.content_url}
      onLoadedMetadata={() => { const element = video.current; if (element && !preview) element.currentTime = Math.min(lesson.position_seconds, Math.max(0, element.duration - 0.1)); }}
      onTimeUpdate={() => void savePosition()} onPause={() => void savePosition(true)} onEnded={() => void savePosition(true)}
      onError={() => setPlaybackError("Verifique o formato do arquivo ou tente abrir a aula novamente.")}
    />}
    {preview ? <p>Prévia do professor — não registra progresso.</p> : saved !== null && <small role="status">Progresso salvo: {Math.floor(saved)}s</small>}
    {saveError && <p role="alert">{saveError} <button onClick={() => void savePosition(true)} type="button">Tentar salvar novamente</button></p>}
  </div>;
}
