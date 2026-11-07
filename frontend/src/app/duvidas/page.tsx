"use client";

import { use, useEffect, useState, type FormEvent } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { enrolledCourse } from "@/data/courses";
import { initialProfile } from "@/data/profile";
import { apiFetch, type ApiQuestion } from "@/lib/engagementApi";
import styles from "./page.module.css";

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
  const [questions, setQuestions] = useState<ApiQuestion[]>([]);
  const [notice, setNotice] = useState("");
  const selectedLesson = enrolledCourse.lessons.find((item) => item.id === lessonId);

  useEffect(() => {
    let active = true;
    apiFetch<ApiQuestion[]>("/api/questions/me")
      .then((data) => {
        if (active) setQuestions(data);
      })
      .catch((err) => {
        if (active) {
          setNotice(err instanceof Error ? `Erro ao carregar dúvidas: ${err.message}` : "Erro ao carregar dúvidas.");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = questionText.trim();
    if (!prompt) return;
    setNotice("");

    try {
      const created = await apiFetch<ApiQuestion>("/api/questions", {
        method: "POST",
        body: JSON.stringify({
          course_id: enrolledCourse.id,
          lesson_id: selectedLesson?.id ?? null,
          prompt,
        }),
      });
      setQuestions((prev) => [created, ...prev]);
      setQuestionText("");
      setNotice("Sua dúvida foi enviada ao professor.");
    } catch (err) {
      setNotice(
        err instanceof Error ? `Erro ao enviar dúvida: ${err.message}` : "Erro ao enviar dúvida."
      );
    }
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
            {questions.map((discussion) => (
              <article className={styles.discussion} key={discussion.id}>
                <div className={styles.discussionMeta}>
                  <span className={`${styles.status} ${discussion.answer ? styles.answered : styles.pending}`}>
                    {discussion.answer ? "Respondida" : "Pendente"}
                  </span>
                  <span>Matéria: {discussion.course_title} • {discussion.lesson_title}</span>
                  <time>{new Date(discussion.created_at).toLocaleDateString("pt-BR")}</time>
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
                      <strong>{discussion.teacher_name}:</strong>
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
