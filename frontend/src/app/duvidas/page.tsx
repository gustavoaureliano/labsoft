"use client";

import { use, useEffect, useState, type FormEvent } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { enrolledCourse } from "@/data/courses";
import { initialProfile } from "@/data/profile";
import { apiFetch, type ApiQuestion } from "@/lib/engagementApi";
import { isApiConfigured } from "@/lib/apiClient";
import { useApi, type Course } from "@/lib/api/learning";
import styles from "./page.module.css";

type StudentDoubtsProps = {
  searchParams: Promise<{ curso?: string | string[]; aula?: string | string[]; duvida?: string | string[] }>;
};

function firstParam(value?: string | string[]) {
  return Array.isArray(value) ? value[0] : value;
}

export default function StudentDoubts({ searchParams }: StudentDoubtsProps) {
  const query = use(searchParams);
  const requestedCourseId = firstParam(query.curso);
  const requestedLessonId = firstParam(query.aula);
  const highlightedQuestionId = firstParam(query.duvida) ?? null;
  const {data: availableCourses, error: coursesError} = useApi<Course[]>(isApiConfigured ? "/api/learning/courses" : null);
  const [courseId, setCourseId] = useState(isApiConfigured ? requestedCourseId ?? "" : enrolledCourse.id);
  const currentCourseId = courseId || (isApiConfigured ? availableCourses?.[0]?.id ?? "" : enrolledCourse.id);
  const currentCourse = isApiConfigured ? availableCourses?.find(item => item.id === currentCourseId) : null;
  const lessonOptions = isApiConfigured ? currentCourse?.lessons ?? [] : enrolledCourse.lessons;
  const initialLessonId = requestedCourseId === enrolledCourse.id && enrolledCourse.lessons.some((item) => item.id === requestedLessonId)
    ? requestedLessonId
    : isApiConfigured && requestedLessonId ? requestedLessonId : "";
  const [lessonId, setLessonId] = useState(initialLessonId);
  const [questionText, setQuestionText] = useState("");
  const [questions, setQuestions] = useState<ApiQuestion[]>([]);
  const [notice, setNotice] = useState("");
  const selectedLesson = lessonOptions.find((item) => item.id === lessonId);

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

  // Notification deep links (?duvida=<id>) point to one of the student's questions.
  useEffect(() => {
    if (!highlightedQuestionId || !questions.some((item) => item.id === highlightedQuestionId)) return;
    document.getElementById(`duvida-${highlightedQuestionId}`)?.scrollIntoView({ block: "center" });
  }, [highlightedQuestionId, questions]);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = questionText.trim();
    if (!prompt || !currentCourseId || (isApiConfigured && !currentCourse)) return;
    setNotice("");

    try {
      const created = await apiFetch<ApiQuestion>("/api/questions", {
        method: "POST",
        body: JSON.stringify({
          course_id: currentCourseId,
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
          {coursesError && <p role="alert">Cursos indisponíveis: {coursesError}</p>}
          <form onSubmit={submitQuestion}>
            <div className={styles.selects}>
              <label>
                <span className={styles.visuallyHidden}>Curso</span>
                <select name="course" value={currentCourseId} onChange={event => {setCourseId(event.target.value);setLessonId("");}}>
                  {isApiConfigured ? availableCourses?.map(item => <option key={item.id} value={item.id}>{item.title}</option>) : <option value={enrolledCourse.id}>{enrolledCourse.title}</option>}
                </select>
              </label>
              <label>
                <span className={styles.visuallyHidden}>Aula</span>
                <select name="lesson" onChange={(event) => setLessonId(event.target.value)} value={lessonId}>
                  <option value="">Dúvida geral sobre o curso</option>
                  {lessonOptions.map((lessonOption) => <option key={lessonOption.id} value={lessonOption.id}>Aula {"number" in lessonOption ? lessonOption.number : String(lessonOption.position).padStart(2,"0")} — {lessonOption.title}</option>)}
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
              {!isApiConfigured && <p>Seu plano Mensal garante respostas em até 24 horas úteis.</p>}
              <button className={styles.primaryButton} type="submit" disabled={isApiConfigured && (!currentCourse || Boolean(coursesError))}>Enviar Pergunta</button>
            </div>
            <p className={styles.notice} aria-live="polite" role="status">{notice}</p>
          </form>
        </section>

        <section className={styles.discussions} aria-labelledby="discussions-title">
          <h2 id="discussions-title">Minhas dúvidas recentes</h2>
          <div className={styles.discussionList}>
            {questions.map((discussion) => (
              <article
                className={`${styles.discussion} ${discussion.id === highlightedQuestionId ? styles.highlighted : ""}`}
                id={`duvida-${discussion.id}`}
                key={discussion.id}
                aria-current={discussion.id === highlightedQuestionId ? "true" : undefined}
              >
                <div className={styles.discussionMeta}>
                  <span className={`${styles.status} ${discussion.answer ? styles.answered : styles.pending}`}>
                    {discussion.answer ? "Respondida" : "Pendente"}
                  </span>
                  <span>Matéria: {discussion.course_title} • {discussion.lesson_title}</span>
                  <time>{new Date(discussion.created_at).toLocaleDateString("pt-BR")}</time>
                </div>
                <div className={styles.message}>
                    <span className={styles.studentMark} aria-hidden="true">{isApiConfigured ? discussion.student_name.slice(0,1) : initialProfile.nickname.slice(0, 1)}</span>
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
