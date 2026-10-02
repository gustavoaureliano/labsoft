"use client";

import { useState, type FormEvent } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { catalogCourses } from "@/data/catalog";
import { initialProfile } from "@/data/profile";
import styles from "./page.module.css";

type Discussion = {
  id: number;
  course: string;
  lesson: string;
  createdAt: string;
  prompt: string;
  answer?: string;
};

const lessonsByCourse: Record<string, string[]> = {
  "fisica-quantica": ["Aula 1 - Introdução à Física Quântica", "Aula 2 - Dualidade Onda-Partícula"],
  "biologia-celular": ["Aula 4 - Organelas Citoplasmáticas", "Aula 6 - Citoesqueleto e Movimento"],
};

const initialDiscussions: Discussion[] = [
  {
    id: 1,
    course: "Física Quântica",
    lesson: "Aula 1",
    createdAt: "Há 2 horas",
    prompt: "Professor, não entendi muito bem como a constante de Planck é usada para calcular a energia dos fótons na fórmula E = hf. Poderia dar um exemplo prático aplicado?",
    answer: "Olá, Bob! Excelente pergunta. Pense na constante h como o menor “pacote” possível de energia. No ENEM, eles costumam pedir para calcular isso usando a frequência da luz visível. Por exemplo, se uma luz vermelha tem frequência 4.3x10¹⁴ Hz, multiplicamos esse valor por 6.63x10⁻³⁴ J·s (que é o h°), dando aproximadamente 2.85x10⁻¹⁹ Joules por fóton. Ficou mais claro?",
  },
  {
    id: 2,
    course: "Biologia Celular para Vestibulares",
    lesson: "Aula 4",
    createdAt: "Há 1 dia",
    prompt: "Quais as principais diferenças que caem na FUVEST sobre o retículo endoplasmático liso e o rugoso? Sempre me confundo em relação à síntese de lipídios.",
  },
];

export default function StudentDoubts() {
  const defaultCourse = catalogCourses[0];
  const [courseId, setCourseId] = useState(defaultCourse.id);
  const [lesson, setLesson] = useState(lessonsByCourse[defaultCourse.id][0]);
  const [questionText, setQuestionText] = useState("");
  const [discussions, setDiscussions] = useState(initialDiscussions);
  const [notice, setNotice] = useState("");
  const selectedCourse = catalogCourses.find((course) => course.id === courseId) ?? defaultCourse;
  const availableLessons = lessonsByCourse[courseId] ?? ["Aula 1 - Introdução ao curso", "Aula 2 - Conceitos fundamentais"];

  function selectCourse(nextCourseId: string) {
    setCourseId(nextCourseId);
    setLesson((lessonsByCourse[nextCourseId] ?? ["Aula 1 - Introdução ao curso"])[0]);
  }

  function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = questionText.trim();
    if (!prompt) return;

    setDiscussions((current) => [{
      id: Date.now(),
      course: selectedCourse.title,
      lesson: lesson.split(" - ")[0],
      createdAt: "Agora",
      prompt,
    }, ...current]);
    setQuestionText("");
    setNotice("Sua dúvida foi enviada ao professor.");
  }

  return (
    <AppShell activePage="doubts" account="student" pageTitle="Dúvidas ao Professor" showSearch={false}>
      <div className={styles.page}>
        <section className={styles.compose} aria-labelledby="compose-title">
          <h1 id="compose-title">Enviar nova dúvida ao professor</h1>
          <form onSubmit={submitQuestion}>
            <div className={styles.selects}>
              <label>
                <span className={styles.visuallyHidden}>Curso</span>
                <select name="course" onChange={(event) => selectCourse(event.target.value)} value={courseId}>
                  {catalogCourses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}
                </select>
              </label>
              <label>
                <span className={styles.visuallyHidden}>Aula</span>
                <select name="lesson" onChange={(event) => setLesson(event.target.value)} value={lesson}>
                  {availableLessons.map((lessonOption) => <option key={lessonOption} value={lessonOption}>{lessonOption}</option>)}
                </select>
              </label>
            </div>
            <label className={styles.visuallyHidden} htmlFor="question-text">Sua dúvida</label>
            <textarea
              id="question-text"
              maxLength={1200}
              onChange={(event) => setQuestionText(event.target.value)}
              placeholder="Escreva detalhadamente a sua dúvida aqui. Você pode incluir fórmulas, minutos do vídeo ou referências de apostilas..."
              required
              value={questionText}
            />
            <div className={styles.composeFooter}>
              <p>Seu plano Mensal garante respostas em até 24 horas úteis.</p>
              <button className={styles.primaryButton} type="submit">Enviar Pergunta</button>
            </div>
            <p className={styles.notice} aria-live="polite" role="status">{notice}</p>
          </form>
        </section>

        <section className={styles.discussions} aria-labelledby="discussions-title">
          <h2 id="discussions-title">Minhas Discussões Recentes</h2>
          <div className={styles.discussionList}>
            {discussions.map((discussion) => (
              <article className={styles.discussion} key={discussion.id}>
                <div className={styles.discussionMeta}>
                  <span className={`${styles.status} ${discussion.answer ? styles.answered : styles.pending}`}>
                    {discussion.answer ? "Respondida" : "Pendente"}
                  </span>
                  <span>Matéria: {discussion.course} • {discussion.lesson}</span>
                  <time>{discussion.createdAt}</time>
                </div>
                <div className={styles.message}>
                  <span className={styles.studentMark} aria-hidden="true">{initialProfile.nickname.slice(0, 1)}</span>
                  <div>
                    <strong>Sua Dúvida:</strong>
                    <p>{discussion.prompt}</p>
                  </div>
                </div>
                {discussion.answer && (
                  <div className={styles.answer}>
                    <span className={styles.teacherMark} aria-hidden="true">F</span>
                    <div>
                      <strong>Prof. Fulano da Silva:</strong>
                      <p>{discussion.answer}</p>
                    </div>
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
