"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { TeacherShell } from "@/components/teacher/TeacherShell";
import { SimpleScreen } from "@/components/ui/SimpleScreen";
import { apiRequest, teacherHeaders } from "@/lib/api/client";
import type { ApiCoursePreview, ApiTeacherDashboard } from "@/lib/api/types";
import styles from "./page.module.css";

export default function GestaoCursos() {
  const [dashboard, setDashboard] = useState<ApiTeacherDashboard | null>(null);
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
  const [preview, setPreview] = useState<ApiCoursePreview | null>(null);
  const [sort, setSort] = useState("recentes");
  const [error, setError] = useState("");
  const courses = dashboard?.items ?? [];
  const orderedCourses = sort === "titulo"
    ? [...courses].sort((a, b) => a.title.localeCompare(b.title, "pt-BR"))
    : courses;

  useEffect(() => {
    apiRequest<ApiTeacherDashboard>("/api/teacher/courses", { headers: teacherHeaders() })
      .then((response) => { setDashboard(response); setError(""); })
      .catch(() => setError("Não foi possível carregar os cursos do professor."));
  }, []);

  async function toggleLessons(courseId: string) {
    if (selectedCourse === courseId) {
      setSelectedCourse(null);
      setPreview(null);
      return;
    }
    setSelectedCourse(courseId);
    setPreview(null);
    try {
      setPreview(await apiRequest<ApiCoursePreview>(`/api/courses/${courseId}/preview`, { headers: teacherHeaders() }));
    } catch {
      setError("Não foi possível carregar as aulas deste curso.");
    }
  }

  return (
    <TeacherShell activePage="courses">
      <SimpleScreen eyebrow="Área do professor" title="Gestão de cursos" description="Acompanhe seus cursos publicados e rascunhos.">
        <div className={styles.summary} aria-label="Resumo dos cursos">
          <article><span>Total de alunos</span><strong>{dashboard?.total_students ?? 0} inscritos</strong></article>
          <article><span>Cursos publicados</span><strong>{dashboard?.published_courses ?? 0}</strong></article>
          <article><span>Rascunhos</span><strong>{dashboard?.draft_courses ?? 0}</strong></article>
        </div>
        {error && <p role="alert">{error}</p>}
        <div className={styles.toolbar}>
          <h2>Meus cursos criados ({courses.length})</h2>
          <label>Ordenar por <select value={sort} onChange={(event) => setSort(event.target.value)}><option value="recentes">Mais recentes</option><option value="titulo">Título</option></select></label>
          <Link href="/professor/cursos/novo">+ Novo curso</Link>
        </div>
        <div className={styles.grid}>
          {orderedCourses.map((course) => (
            <article className={styles.card} key={course.id}>
              <div className={styles.image}><Image src="/images/courses/fisica-quantica.webp" alt="" fill sizes="(max-width: 900px) 100vw, 30vw" /><span>{course.status === "published" ? "Publicado" : "Rascunho"}</span></div>
              <div className={styles.cardContent}>
                <h3>{course.title}</h3>
                <p>{course.student_count} alunos · {course.lesson_count} {course.lesson_count === 1 ? "aula" : "aulas"}</p>
                <div className={styles.actions}>
                  <Link href={`/professor/cursos/${course.id}/editar`}>Editar</Link>
                  <button type="button" onClick={() => toggleLessons(course.id)}>{selectedCourse === course.id ? "Fechar aulas" : "Aulas"}</button>
                </div>
              </div>
            </article>
          ))}
        </div>
        {!dashboard && !error && <p>Carregando cursos...</p>}
        {preview && <section className={styles.lessonPanel} aria-label={`Aulas de ${preview.course.title}`}><h2>Aulas de {preview.course.title}</h2>{preview.lessons.length ? <ol>{preview.lessons.map((lesson) => <li key={lesson.id}>{lesson.title}</li>)}</ol> : <p>Este rascunho ainda não tem aulas.</p>}</section>}
      </SimpleScreen>
    </TeacherShell>
  );
}
