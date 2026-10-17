"use client";

import { useEffect, useRef, useState } from "react";
import { api, jsonRequest, type Playback } from "@/lib/api/learning";

export function VideoPlayer({lesson, preview = false, poster}: {lesson: Playback; preview?: boolean; poster?: string}) {
  const video = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState("");
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
        if (mounted.current) { setSaved(position); setError(""); }
      }
    } catch (error) {
      if (mounted.current) setError(`Progresso não salvo: ${(error as Error).message}`);
    } finally { saving.current = false; }
  }

  return <div>
    <video ref={video} controls preload="metadata" poster={poster} style={{width: "100%", aspectRatio: "16 / 9", background: "#10242d", borderRadius: 8}}
      src={lesson.content_url}
      onLoadedMetadata={() => { const element = video.current; if (element && !preview) element.currentTime = Math.min(lesson.position_seconds, Math.max(0, element.duration - 0.1)); }}
      onTimeUpdate={() => void savePosition()} onPause={() => void savePosition(true)} onEnded={() => void savePosition(true)}
      onError={() => setError("Não foi possível reproduzir este vídeo. Verifique o formato ou recarregue a aula.")}
    />
    {preview ? <p>Prévia do professor — não registra progresso.</p> : saved !== null && <small role="status">Progresso salvo: {Math.floor(saved)}s</small>}
    {error && <p role="alert">{error} <button onClick={() => void savePosition(true)} type="button">Tentar salvar novamente</button></p>}
  </div>;
}
