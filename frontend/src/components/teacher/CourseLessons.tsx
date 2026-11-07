"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, jsonRequest, useApi, type Course, type Lesson } from "@/lib/api/learning";
import { editLessonHref, durationLabel, type LessonNavigationOrigin } from "./lessonLinks";
import { LessonImage } from "./LessonImage";
import styles from "./TeacherLessons.module.css";

export function CourseLessons({ courseId, origin }: { courseId: string; origin?: LessonNavigationOrigin }) {
  const { data, error } = useApi<Course>(`/api/learning/courses/${encodeURIComponent(courseId)}`);
  if (error) return <div className={styles.page}><Link className={styles.back} href={origin === "course-editor" ? `/professor/cursos/${encodeURIComponent(courseId)}/editar` : "/professor/cursos"}>{origin === "course-editor" ? "← Voltar à edição do curso" : "← Voltar aos cursos"}</Link><h1>Aulas indisponíveis</h1><p role="alert" className={styles.error}>{error}</p></div>;
  if (!data) return <p role="status">Carregando aulas...</p>;
  return <CourseLessonsContent key={data.id} initialCourse={data} origin={origin} />;
}

function CourseLessonsContent({ initialCourse, origin }: { initialCourse: Course; origin?: LessonNavigationOrigin }) {
  const [lessons, setLessons] = useState(initialCourse.lessons);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const running = useRef(false);
  const router = useRouter();
  const backHref = origin === "course-editor" ? `/professor/cursos/${encodeURIComponent(initialCourse.id)}/editar` : "/professor/cursos";

  async function run(action: () => Promise<void>) {
    if (running.current) return;
    running.current = true; setBusy(true); setError(""); setMessage("");
    try { await action(); }
    catch (error) { setError((error as Error).message); }
    finally { running.current = false; setBusy(false); }
  }

  async function addLesson() {
    await run(async () => {
      const lesson = await api<Lesson>("/api/learning/lessons", jsonRequest("POST", {
        course_id: initialCourse.id, title: "Nova aula", position: Math.max(0, ...lessons.map(item => item.position)) + 1,
      }));
      // Keep the new record visible even if navigation is interrupted.
      setLessons(current => [...current, lesson]);
      router.push(editLessonHref(initialCourse.id, lesson.id, origin));
    });
  }

  async function move(index: number, direction: number) {
    await run(async () => {
      const ids = lessons.map(lesson => lesson.id);
      [ids[index], ids[index + direction]] = [ids[index + direction], ids[index]];
      const reordered = await api<Lesson[]>(`/api/learning/courses/${initialCourse.id}/lessons/order`, jsonRequest("PUT", { lesson_ids: ids }));
      const existing = new Map(lessons.map(lesson => [lesson.id, lesson]));
      setLessons(reordered.map(lesson => ({ ...existing.get(lesson.id), ...lesson })));
      setMessage("Ordem das aulas salva.");
    });
  }

  return <div className={styles.page}>
    <Link className={styles.back} href={backHref}>{origin === "course-editor" ? "← Voltar à edição do curso" : "← Voltar aos cursos"}</Link>
    <header className={styles.heading}>
      <div><span className={styles.eyebrow}>Gerenciar aulas</span><h1>{initialCourse.title}</h1><p>{lessons.length} {lessons.length === 1 ? "aula" : "aulas"} · Organize a sequência e prepare o conteúdo dos seus alunos.</p></div>
      <button className={styles.primary} disabled={busy} type="button" onClick={() => void addLesson()}>+ Adicionar aula</button>
    </header>
    {busy && <p role="status" className={styles.notice}>Salvando...</p>}
    {message && <p role="status" className={styles.notice}>{message}</p>}
    {error && <p role="alert" className={styles.error}>{error}</p>}
    <ol className={styles.list} aria-label="Aulas do curso" aria-busy={busy}>
      {lessons.map((lesson, index) => <li className={styles.row} key={lesson.id} data-lesson-id={lesson.id}>
        <Link className={styles.cover} href={editLessonHref(initialCourse.id, lesson.id, origin)} tabIndex={-1} aria-hidden="true"><LessonImage source={lesson.thumbnail_url} fallback={initialCourse.image} sizes="128px" alt="" /></Link>
        <div className={styles.copy}><span className={styles.eyebrow}>Aula {String(lesson.position).padStart(2, "0")} · {durationLabel(lesson.duration_seconds)}</span><h2><Link href={editLessonHref(initialCourse.id, lesson.id, origin)}>{lesson.title}</Link></h2><span className={styles.status}>{!lesson.media_id ? "Sem vídeo" : lesson.playable === false ? "Vídeo indisponível" : "Vídeo disponível"}</span></div>
        <div className={styles.actions}>
          <Link className={styles.secondary} href={editLessonHref(initialCourse.id, lesson.id, origin)}>Editar aula</Link>
          {lesson.media_id && lesson.playable !== false && <Link className={styles.secondary} href={editLessonHref(initialCourse.id, lesson.id, origin, true)}>Prévia</Link>}
          <div className={styles.order} aria-label={`Ordenar ${lesson.title}`}>
            <button type="button" disabled={busy || index === 0} aria-label={`Mover aula ${index + 1} para cima`} title="Mover para cima" onClick={() => void move(index, -1)}>↑</button>
            <button type="button" disabled={busy || index === lessons.length - 1} aria-label={`Mover aula ${index + 1} para baixo`} title="Mover para baixo" onClick={() => void move(index, 1)}>↓</button>
          </div>
        </div>
      </li>)}
    </ol>
    {lessons.length === 0 && <section className={styles.empty}><h2>Seu curso começa pela primeira aula</h2><p className={styles.muted}>Adicione uma aula, preencha as informações e envie o vídeo.</p></section>}
  </div>;
}
