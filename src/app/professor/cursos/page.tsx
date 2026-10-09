"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { TeacherShell } from "@/components/teacher/TeacherShell";
import { SimpleScreen } from "@/components/ui/SimpleScreen";
import { initialTeacherCourses, teacherCoursesKey } from "@/data/teacherCourses";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./page.module.css";

export default function GestaoCursos() {
  const [courses] = useDemoStorage(teacherCoursesKey, initialTeacherCourses);
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
  const [sort, setSort] = useState("recentes");
  const orderedCourses = sort === "titulo" ? [...courses].sort((a, b) => a.title.localeCompare(b.title, "pt-BR")) : courses;
  const selected = courses.find((course) => course.id === selectedCourse);

  return (
    <TeacherShell activePage="courses">
      <SimpleScreen eyebrow="Área do professor" title="Gestão de cursos" description="Acompanhe seus cursos publicados e rascunhos.">
        <div className={styles.summary} aria-label="Resumo dos cursos">
          <article><span>Total de alunos</span><strong>18.420 inscritos</strong></article>
          <article><span>Tempo de vídeo publicado</span><strong>142 horas</strong></article>
          <article><span>Dúvidas respondidas</span><strong>98,4% de taxa</strong></article>
        </div>
        <div className={styles.toolbar}>
          <h2>Meus cursos criados ({courses.length})</h2>
          <label>Ordenar por <select value={sort} onChange={(event) => setSort(event.target.value)}><option value="recentes">Mais recentes</option><option value="titulo">Título</option></select></label>
          <Link href="/professor/cursos/novo">+ Novo curso</Link>
        </div>
        <div className={styles.grid}>
          {orderedCourses.map((course) => (
            <article className={styles.card} key={course.id}>
              <div className={styles.image}><Image src={course.image} alt="" fill sizes="(max-width: 900px) 100vw, 30vw" /><span>{course.status}</span></div>
              <div className={styles.cardContent}>
                <h3>{course.title}</h3>
                <p>{course.students} · {course.lessons.length} {course.lessons.length === 1 ? "aula" : "aulas"}</p>
                <div className={styles.actions}>
                  <Link href={`/professor/cursos/${course.id}/editar`}>Editar</Link>
                  <button type="button" onClick={() => setSelectedCourse(selectedCourse === course.id ? null : course.id)}>{selectedCourse === course.id ? "Fechar aulas" : "Aulas"}</button>
                </div>
              </div>
            </article>
          ))}
        </div>
        {selected && <section className={styles.lessonPanel} aria-label={`Aulas de ${selected.title}`}><h2>Aulas de {selected.title}</h2>{selected.lessons.length ? <ol>{selected.lessons.map((lesson) => <li key={lesson.id}>{lesson.title}</li>)}</ol> : <p>Este rascunho ainda não tem aulas.</p>}</section>}
      </SimpleScreen>
    </TeacherShell>
  );
}
