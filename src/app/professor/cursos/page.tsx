"use client";

import { useState } from "react";
import Image from "next/image";
import { TeacherShell } from "@/components/teacher/TeacherShell";
import { SimpleScreen } from "@/components/ui/SimpleScreen";
import styles from "./page.module.css";

const courses = [
  { id: "quantica", title: "Introdução à Física Quântica", status: "Publicado", students: "12.420 alunos", lessons: ["Introdução e contexto histórico", "Radiação de corpo negro", "Efeito fotoelétrico"], image: "/teacher-quantum.png" },
  { id: "termodinamica", title: "Termodinâmica Avançada", status: "Rascunho", students: "Nenhum aluno", lessons: [] as string[], image: "/teacher-thermo.png" },
  { id: "cinematica", title: "Cinemática e Dinâmica para ENEM", status: "Publicado", students: "6.000 alunos", lessons: ["Movimento uniforme", "Leis de Newton"], image: "/teacher-kinematics.png" },
];

export default function GestaoCursos() {
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
  const [sort, setSort] = useState("recentes");
  const [notice, setNotice] = useState("");
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
          <button type="button" onClick={() => setNotice("O Editor de Curso será integrado pelo módulo do João.")}>+ Novo curso</button>
        </div>
        <div className={styles.grid}>
          {orderedCourses.map((course) => (
            <article className={styles.card} key={course.id}>
              <div className={styles.image}><Image src={course.image} alt="" fill sizes="(max-width: 900px) 100vw, 30vw" /><span>{course.status}</span></div>
              <div className={styles.cardContent}>
                <h3>{course.title}</h3>
                <p>{course.students} · {course.lessons.length} {course.lessons.length === 1 ? "aula" : "aulas"}</p>
                <div className={styles.actions}>
                  <button type="button" onClick={() => setNotice("O Editor de Curso será integrado pelo módulo do João.")}>Editar</button>
                  <button type="button" onClick={() => setSelectedCourse(selectedCourse === course.id ? null : course.id)}>{selectedCourse === course.id ? "Fechar aulas" : "Aulas"}</button>
                </div>
              </div>
            </article>
          ))}
        </div>
        {selected && <section className={styles.lessonPanel} aria-label={`Aulas de ${selected.title}`}><h2>Aulas de {selected.title}</h2>{selected.lessons.length ? <ol>{selected.lessons.map((lesson) => <li key={lesson}>{lesson}</li>)}</ol> : <p>Este rascunho ainda não tem aulas.</p>}</section>}
        {notice && <p className={styles.notice} role="status">{notice}</p>}
      </SimpleScreen>
    </TeacherShell>
  );
}
