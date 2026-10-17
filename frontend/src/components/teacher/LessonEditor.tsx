"use client";

import { useState } from "react";
import Image from "next/image";
import { api, jsonRequest, useApi, type Course, type Lesson, type Playback } from "@/lib/api/learning";
import { VideoPlayer } from "@/components/learning/VideoPlayer";
import styles from "./CourseEditor.module.css";

function LessonPreview({id}: {id: string}) {
  const {data, error} = useApi<Playback>(`/api/learning/lessons/${id}/playback`);
  if (error) return <p role="alert">{error}</p>;
  return data ? <VideoPlayer key={data.media_id} lesson={data} preview /> : <p>Carregando prévia...</p>;
}

function LessonRow({lesson, index, total, busy, run, move}: {lesson: Lesson; index: number; total: number; busy: boolean; run: (action: () => Promise<unknown>) => Promise<void>; move: (index: number, direction: number) => Promise<void>}) {
  const [title, setTitle] = useState(lesson.title);
  const [description, setDescription] = useState(lesson.description);
  const [preview, setPreview] = useState(false);
  const base = `/api/learning/lessons/${lesson.id}`;
  async function upload(file: File, thumbnail: boolean) {
    const data = new FormData(); data.set("file", file);
    const media = await api<{id: string}>(thumbnail ? "/api/media/thumbnails" : "/api/media", {method: "POST", body: data});
    await api(base + (thumbnail ? "/thumbnail" : "/media"), jsonRequest("PATCH", {media_id: media.id}));
  }
  return <article className={styles.card} aria-label={`Aula ${index + 1}`}>
    <h3>Aula {index + 1}: {lesson.title}</h3>
    <div className={styles.formGrid}>
      <label>Título da aula<input value={title} onChange={event => setTitle(event.target.value)} disabled={busy} /></label>
      <label>Descrição da aula<textarea value={description} onChange={event => setDescription(event.target.value)} disabled={busy} /></label>
      <label>Vídeo da aula<input aria-label={`Enviar vídeo da aula ${index + 1}`} type="file" accept="video/mp4,video/webm" disabled={busy} onChange={event => {const file = event.target.files?.[0]; if (file) void run(() => upload(file, false)); event.target.value = "";}} /><small>{lesson.media_id ? `Vídeo associado · ${lesson.duration_seconds ?? "?"}s` : "Nenhum vídeo associado"}</small></label>
      <label>Thumbnail da aula<input aria-label={`Enviar thumbnail da aula ${index + 1}`} type="file" accept="image/png,image/jpeg" disabled={busy} onChange={event => {const file = event.target.files?.[0]; if (file) void run(() => upload(file, true)); event.target.value = "";}} /></label>
    </div>
    <div className={styles.rowActions}>
      <button type="button" disabled={busy || !title.trim()} onClick={() => void run(() => api(base, jsonRequest("PATCH", {title, description})))}>Salvar aula</button>
      <button type="button" disabled={busy || index === 0} onClick={() => void move(index, -1)} aria-label={`Mover aula ${index + 1} para cima`}>↑</button>
      <button type="button" disabled={busy || index === total - 1} onClick={() => void move(index, 1)} aria-label={`Mover aula ${index + 1} para baixo`}>↓</button>
      <button type="button" disabled={busy} onClick={() => {if (window.confirm("Excluir esta aula? O arquivo será preservado.")) void run(() => api(base, {method: "DELETE"}));}}>Excluir aula</button>
      {lesson.media_id && <><button type="button" disabled={busy} onClick={() => void run(() => api(base + "/media", jsonRequest("PATCH", {media_id: null})))}>Remover vídeo</button><button type="button" onClick={() => setPreview(!preview)}>Prévia da aula</button></>}
      {lesson.thumbnail_id && <button type="button" disabled={busy} onClick={() => void run(() => api(base + "/thumbnail", jsonRequest("PATCH", {media_id: null})))}>Remover thumbnail</button>}
    </div>
    {lesson.thumbnail_url && <Image unoptimized src={lesson.thumbnail_url} alt={`Thumbnail de ${lesson.title}`} width={160} height={90} />}
    {preview && <LessonPreview id={lesson.id} />}
  </article>;
}

export function LessonEditor({courseId}: {courseId: string}) {
  const [version, setVersion] = useState(0);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const {data: course, error} = useApi<Course>(`/api/learning/courses/${courseId}?v=${version}`);
  async function run(action: () => Promise<unknown>) {
    if (busy) return;
    setBusy(true); setNotice("");
    try { await action(); setNotice("Alteração salva no backend."); setVersion(value => value + 1); }
    catch (error) {setNotice((error as Error).message);}
    finally {setBusy(false);}
  }
  async function move(index: number, direction: number) {
    if (!course) return;
    const ids = course.lessons.map(lesson => lesson.id);
    [ids[index], ids[index + direction]] = [ids[index + direction], ids[index]];
    await run(() => api(`/api/learning/courses/${courseId}/lessons/order`, jsonRequest("PUT", {lesson_ids: ids})));
  }
  if (error) return <section className={styles.card}><h2>Aulas</h2><p role="alert">{error}</p><p>O curso precisa estar disponível no contrato de cursos do backend.</p></section>;
  return <section aria-labelledby="lessons-title">
    <div className={styles.sectionHeading}><div><h2 id="lessons-title">2. Aulas</h2><p>Aulas e arquivos são salvos no backend, independentemente do formulário demonstrativo do curso.</p></div><button type="button" disabled={busy || !course} onClick={() => void run(() => api("/api/learning/lessons", jsonRequest("POST", {course_id: courseId, title: "Nova aula", position: Math.max(0, ...(course?.lessons.map(lesson => lesson.position) ?? [])) + 1})))}>+ Adicionar aula</button></div>
    {busy && <p role="status">Salvando...</p>}{notice && <p role="status">{notice}</p>}
    {!course ? <p>Carregando aulas...</p> : course.lessons.map((lesson, index) => <LessonRow key={`${lesson.id}:${version}`} lesson={lesson} index={index} total={course.lessons.length} busy={busy} run={run} move={move} />)}
    {course?.lessons.length === 0 && <p>Nenhuma aula adicionada.</p>}
    <p>Upload cancelado ou substituído pode ficar sem associação; arquivos antigos não são excluídos automaticamente.</p>
  </section>;
}
