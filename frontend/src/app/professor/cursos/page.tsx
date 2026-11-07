"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { TeacherShell } from "@/components/teacher/TeacherShell";
import { SimpleScreen } from "@/components/ui/SimpleScreen";
import { initialTeacherCourses, teacherCoursesKey } from "@/data/teacherCourses";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { useApi, type Course } from "@/lib/api/learning";
import styles from "./page.module.css";

export default function GestaoCursos() {
  const [courses] = useDemoStorage(teacherCoursesKey, initialTeacherCourses);
  const backend = useApi<Course[]>("/api/learning/courses");
  const [sort, setSort] = useState("recentes");
  const orderedCourses = sort === "titulo" ? [...courses].sort((a, b) => a.title.localeCompare(b.title, "pt-BR")) : courses;

  return (
    <TeacherShell activePage="courses">
      <SimpleScreen eyebrow="Área do professor" title="Gestão de cursos" description="Acompanhe seus cursos publicados e rascunhos.">
        {backend.error && <p role="alert">Aulas reais indisponíveis: {backend.error}. Listagens locais abaixo são demonstrativas.</p>}
        <div className={styles.summary} aria-label="Resumo demonstrativo dos cursos">
          <article><span>Total de alunos</span><strong>18.420 inscritos</strong></article>
          <article><span>Tempo de vídeo publicado</span><strong>5h 51min</strong></article>
          <article><span>Dúvidas respondidas</span><strong>98,4% de taxa</strong></article>
        </div>
        <p className={styles.notice}>Indicadores demonstrativos. As aulas dos cursos integrados são salvas na plataforma.</p>
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
                 <p>{course.students} · {backend.data?.find(item => item.id === course.id)?.lessons.length ?? course.lessons.length} aulas{backend.data?.some(item => item.id === course.id) ? "" : " demonstrativas"}</p>
                <div className={styles.actions}>
                  {course.id.startsWith("curso-") ? <Link className={styles.primaryAction} href={`/professor/cursos/${course.id}/editar`}>Editar rascunho demo</Link> : <Link className={styles.primaryAction} href={`/professor/cursos/${course.id}/aulas`}>Gerenciar aulas</Link>}
                  {!course.id.startsWith("curso-") && <Link href={`/professor/cursos/${course.id}/editar`}>Editar informações</Link>}
                </div>
              </div>
            </article>
          ))}
        </div>
      </SimpleScreen>
    </TeacherShell>
  );
}
