"use client";

import { useEffect, useRef, useState, type FormEvent, type MouseEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, jsonRequest, useApi, type Course, type Lesson, type Playback } from "@/lib/api/learning";
import { VideoPlayer } from "@/components/learning/VideoPlayer";
import { courseLessonsHref, durationLabel, type LessonNavigationOrigin } from "./lessonLinks";
import { LessonImage } from "./LessonImage";
import styles from "./TeacherLessons.module.css";

type Media = { id: string; original_filename: string; duration_seconds: number | null };

function FilePicker({ label, accept, disabled, onSelect }: { label: string; accept: string; disabled: boolean; onSelect: (file: File) => void }) {
  return <label className={styles.fileButton}>{label}<input className={styles.fileInput} type="file" aria-label={label} accept={accept} disabled={disabled} onChange={event => {
    const file = event.target.files?.[0];
    if (file) onSelect(file);
    event.target.value = "";
  }} /></label>;
}

function LessonPreview({ lesson, poster, title, description }: { lesson: Lesson; poster: string; title: string; description: string }) {
  const { data, error } = useApi<Playback>(lesson.media_id ? `/api/learning/lessons/${lesson.id}/playback?media=${lesson.media_id}` : null);
  if (!lesson.media_id) return <section className={styles.empty}><h2>Adicione um vídeo para visualizar a aula</h2><p className={styles.muted}>Volte para Editar e selecione um arquivo MP4 ou WebM.</p></section>;
  if (error) return <p role="alert" className={styles.error}>{error}</p>;
  if (!data) return <p role="status">Carregando prévia...</p>;
  return <section className={styles.preview} aria-label="Prévia da aula"><VideoPlayer key={data.media_id} lesson={data} preview poster={poster} /><div className={styles.card}><h2>{title || "Aula sem título"}</h2><p>{description || "Adicione uma descrição para apresentar esta aula."}</p></div></section>;
}

export function LessonEditor({ courseId, lessonId, initialPreview = false, origin }: { courseId: string; lessonId: string; initialPreview?: boolean; origin?: LessonNavigationOrigin }) {
  const { data, error } = useApi<Course>(`/api/learning/courses/${encodeURIComponent(courseId)}`);
  if (error) return <div className={styles.page}><Link className={styles.back} href={courseLessonsHref(courseId, origin)}>← Voltar às aulas</Link><p role="alert" className={styles.error}>{error}</p></div>;
  if (!data) return <p role="status">Carregando aula...</p>;
  const lesson = data.lessons.find(item => item.id === lessonId);
  if (!lesson) return <div className={styles.page}><h1>Aula não encontrada neste curso</h1><Link className={styles.back} href={courseLessonsHref(courseId, origin)}>Voltar às aulas</Link></div>;
  return <LessonForm key={lesson.id} course={data} initialLesson={lesson} initialPreview={initialPreview} origin={origin} />;
}

function LessonForm({ course, initialLesson, initialPreview, origin }: { course: Course; initialLesson: Lesson; initialPreview: boolean; origin?: LessonNavigationOrigin }) {
  const [lesson, setLesson] = useState(initialLesson);
  const [title, setTitle] = useState(initialLesson.title);
  const [description, setDescription] = useState(initialLesson.description);
  const [preview, setPreview] = useState(initialPreview);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const running = useRef(false);
  const router = useRouter();
  const base = `/api/learning/lessons/${lesson.id}`;
  const dirty = title !== lesson.title || description !== lesson.description;
  const media = useApi<Media>(lesson.media_id ? `/api/media/${lesson.media_id}` : null);
  const thumbnail = useApi<Media>(lesson.thumbnail_id ? `/api/media/${lesson.thumbnail_id}` : null);
  const poster = lesson.thumbnail_id ? `/api/media/${lesson.thumbnail_id}/content` : course.image;

  useEffect(() => {
    if (!dirty && !busy) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, busy]);

  async function run(message: string, action: () => Promise<void>) {
    if (running.current) return;
    running.current = true; setBusy(message); setNotice(""); setError("");
    try { await action(); }
    catch (error) { setError((error as Error).message); }
    finally { running.current = false; setBusy(""); }
  }

  function back(event: MouseEvent<HTMLAnchorElement>) {
    if (busy || (dirty && !window.confirm("Sair sem salvar as informações desta aula?"))) event.preventDefault();
  }

  function save(event: FormEvent) {
    event.preventDefault();
    void run("Salvando informações...", async () => {
      const updated = await api<Lesson>(base, jsonRequest("PATCH", { title, description }));
      setLesson(current => ({ ...current, ...updated }));
      setTitle(updated.title); setDescription(updated.description);
      setNotice("Informações da aula salvas.");
    });
  }

  async function upload(file: File, image: boolean) {
    await run(image ? "Enviando imagem..." : "Enviando e verificando vídeo...", async () => {
      const body = new FormData(); body.set("file", file);
      const uploaded = await api<Media>(image ? "/api/media/thumbnails" : "/api/media", { method: "POST", body });
      const updated = await api<Lesson>(base + (image ? "/thumbnail" : "/media"), jsonRequest("PATCH", { media_id: uploaded.id }));
      // Refresh only persisted media fields; the title/description draft stays mounted.
      setLesson(current => ({ ...current, ...updated, duration_seconds: image ? current.duration_seconds : uploaded.duration_seconds }));
      setNotice(image ? "Imagem atualizada." : "Vídeo atualizado.");
    });
  }

  async function detach(image: boolean) {
    await run("Atualizando arquivo...", async () => {
      const updated = await api<Lesson>(base + (image ? "/thumbnail" : "/media"), jsonRequest("PATCH", { media_id: null }));
      setLesson(current => ({ ...current, ...updated, duration_seconds: image ? current.duration_seconds : null }));
      setNotice(image ? "A imagem padrão do curso está em uso." : "Vídeo removido desta aula.");
    });
  }

  async function removeLesson() {
    if (!window.confirm("Excluir esta aula? O vídeo será preservado no armazenamento.")) return;
    await run("Excluindo aula...", async () => {
      await api(base, { method: "DELETE" });
      router.replace(courseLessonsHref(course.id, origin));
    });
  }

  return <div className={styles.page}>
    <Link className={styles.back} href={courseLessonsHref(course.id, origin)} onClick={back}>← Voltar às aulas</Link>
    <header className={styles.heading}><div><span className={styles.eyebrow}>{course.title} · Aula {String(lesson.position).padStart(2, "0")}</span><h1>{lesson.title}</h1><p>Prepare o conteúdo e confira como a aula será apresentada.</p></div><span className={styles.status}>{lesson.media_id ? "Vídeo associado" : "Sem vídeo"}</span></header>
    <nav className={styles.switcher} aria-label="Modo do editor"><button type="button" aria-pressed={!preview} onClick={() => setPreview(false)}>Editar</button><button type="button" aria-pressed={preview} onClick={() => setPreview(true)}>Prévia</button></nav>
    {busy && <p role="status" className={styles.notice}>{busy}</p>}
    {notice && <p role="status" className={styles.notice}>{notice}</p>}
    {error && <p role="alert" className={styles.error}>{error}</p>}
    {preview ? <>
      <p className={styles.muted}>{dirty ? "Prévia com suas alterações de texto ainda não salvas. Volte para Editar para salvá-las." : "Você está visualizando a aula como professor. Seu progresso não será alterado."}</p>
      <LessonPreview lesson={lesson} poster={poster} title={title} description={description} />
    </> : <>
      <form id="lesson-information" className={styles.card} onSubmit={save} aria-labelledby="lesson-info-title">
        <h2 id="lesson-info-title">Informações da aula</h2>
        <div className={styles.form}><label className={styles.field}>Título<input name="lesson-title" value={title} onChange={event => setTitle(event.target.value)} maxLength={255} required disabled={Boolean(busy)} /></label><label className={styles.field}>Descrição<textarea name="lesson-description" value={description} onChange={event => setDescription(event.target.value)} rows={4} disabled={Boolean(busy)} placeholder="O que o aluno vai aprender nesta aula?" /></label></div>
      </form>
      <div className={styles.mediaGrid}>
        <section className={styles.card} aria-labelledby="lesson-video-title"><h2 id="lesson-video-title">Vídeo</h2><p className={styles.muted}>MP4 ou WebM · Até 100 MiB</p><div className={styles.fileInfo}><strong>{lesson.media_id ? media.data?.original_filename ?? "Vídeo associado" : "Nenhum vídeo enviado"}</strong><small>{lesson.media_id ? durationLabel(media.data?.duration_seconds ?? lesson.duration_seconds) : "Selecione o arquivo da sua aula."}</small>{media.error && <small role="alert">{media.error}</small>}</div><div className={styles.actions}><FilePicker label={lesson.media_id ? "Trocar vídeo" : "Enviar vídeo"} accept="video/mp4,video/webm" disabled={Boolean(busy)} onSelect={file => void upload(file, false)} />{lesson.media_id && <button className={styles.textButton} type="button" disabled={Boolean(busy)} onClick={() => void detach(false)}>Remover vídeo</button>}</div></section>
        <section className={styles.card} aria-labelledby="lesson-thumbnail-title"><h2 id="lesson-thumbnail-title">Imagem de apresentação</h2><p className={styles.muted}>{lesson.thumbnail_id ? thumbnail.data?.original_filename ?? "Imagem personalizada" : "Usando a imagem do curso"}</p><div className={styles.thumbnail}><LessonImage source={poster} fallback={course.image} alt="Imagem de apresentação da aula" sizes="240px" /></div><div className={styles.actions}><FilePicker label="Trocar imagem" accept="image/png,image/jpeg" disabled={Boolean(busy)} onSelect={file => void upload(file, true)} />{lesson.thumbnail_id && <button type="button" className={styles.textButton} disabled={Boolean(busy)} onClick={() => void detach(true)}>Usar imagem padrão</button>}</div><p className={styles.muted}>JPEG ou PNG · Até 5 MiB</p>{thumbnail.error && <p role="alert">{thumbnail.error}</p>}</section>
      </div>
      <p className={styles.muted}>Arquivos são atualizados assim que o envio termina. O título e a descrição só mudam ao salvar as informações.</p>
      <div className={styles.footer}><span className={styles.muted}>{dirty ? "Você tem alterações de texto não salvas." : "Informações salvas."}</span><div className={styles.actions}><Link className={styles.secondary} href={courseLessonsHref(course.id, origin)} onClick={back}>Voltar às aulas</Link><button className={styles.primary} type="submit" form="lesson-information" disabled={Boolean(busy) || !title.trim() || !dirty}>Salvar informações</button></div></div>
      <div className={styles.dangerZone}><span className={styles.muted}>Excluir a aula não apaga o arquivo de vídeo.</span><button type="button" className={styles.danger} disabled={Boolean(busy)} onClick={() => void removeLesson()}>Excluir aula</button></div>
    </>}
  </div>;
}
