"use client";

import { use, useState, type FormEvent } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { enrolledCourse } from "@/data/courses";
import { initialProfile } from "@/data/profile";
import { questionsDemoKey, type DemoQuestion } from "@/data/questionsDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./page.module.css";

type Discussion = {
  id: number;
  course: string;
  lesson: string;
  createdAt: string;
  prompt: string;
  answer?: string;
};

const initialDiscussions: Discussion[] = [
  {
    id: 1,
    course: enrolledCourse.title,
    lesson: "Aula 08 — Leis de Newton e suas aplicações",
    createdAt: "Há 2 horas",
    prompt: "Como identifico a força resultante quando o exercício mostra várias forças em sentidos diferentes?",
    answer: "Escolha um sentido positivo, some as forças nesse sentido e subtraia as forças no sentido contrário. O resultado com sinal indica o sentido da força resultante.",
  },
  {
    id: 2,
    course: enrolledCourse.title,
    lesson: "Aula 10 — Trabalho e energia",
    createdAt: "Há 1 dia",
    prompt: "Quando o trabalho de uma força deve ser considerado negativo?",
  },
];

type StudentDoubtsProps = {
  searchParams: Promise<{ curso?: string | string[]; aula?: string | string[] }>;
};

function firstParam(value?: string | string[]) {
  return Array.isArray(value) ? value[0] : value;
}

export default function StudentDoubts({ searchParams }: StudentDoubtsProps) {
  const query = use(searchParams);
  const requestedCourseId = firstParam(query.curso);
  const requestedLessonId = firstParam(query.aula);
  const initialLessonId = requestedCourseId === enrolledCourse.id && enrolledCourse.lessons.some((item) => item.id === requestedLessonId)
    ? requestedLessonId
    : "";
  const [lessonId, setLessonId] = useState(initialLessonId);
  const [questionText, setQuestionText] = useState("");
  const discussions = initialDiscussions;
  const [sharedQuestions, saveSharedQuestions] = useDemoStorage<DemoQuestion[]>(questionsDemoKey, []);
  const [notice, setNotice] = useState("");
  const selectedLesson = enrolledCourse.lessons.find((item) => item.id === lessonId);

  function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = questionText.trim();
    if (!prompt) return;

    saveSharedQuestions([{
      id: Date.now(),
      student: initialProfile.nickname,
      courseId: enrolledCourse.id,
      course: enrolledCourse.title,
      lessonId: selectedLesson?.id,
      lesson: selectedLesson ? `Aula ${selectedLesson.number} — ${selectedLesson.title}` : "Dúvida geral sobre o curso",
      prompt,
    }, ...sharedQuestions]);
    setQuestionText("");
    setNotice("Sua dúvida foi enviada ao professor.");
  }

  return (
    <AppShell activePage="doubts">
      <div className={styles.page}>
        <section className={styles.compose} aria-labelledby="compose-title">
          <h1 id="compose-title">Enviar nova dúvida ao professor</h1>
          <p className={styles.composeDescription}>Esta conversa fica entre você e o professor. Selecione uma aula ou envie uma dúvida geral sobre o curso.</p>
          <form onSubmit={submitQuestion}>
            <div className={styles.selects}>
              <label>
                <span className={styles.visuallyHidden}>Curso</span>
                <select name="course" defaultValue={enrolledCourse.id}>
                  <option value={enrolledCourse.id}>{enrolledCourse.title}</option>
                </select>
              </label>
              <label>
                <span className={styles.visuallyHidden}>Aula</span>
                <select name="lesson" onChange={(event) => setLessonId(event.target.value)} value={lessonId}>
                  <option value="">Dúvida geral sobre o curso</option>
                  {enrolledCourse.lessons.map((lessonOption) => <option key={lessonOption.id} value={lessonOption.id}>Aula {lessonOption.number} — {lessonOption.title}</option>)}
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
          <h2 id="discussions-title">Minhas dúvidas recentes</h2>
          <div className={styles.discussionList}>
            {[...sharedQuestions.map((question) => ({ ...question, createdAt: "Agora" })), ...discussions].map((discussion) => (
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
                    <span className={styles.teacherMark} aria-hidden="true">MA</span>
                    <div>
                      <strong>{enrolledCourse.teacher}:</strong>
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
