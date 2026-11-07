"use client";

import { useEffect, useState, type FormEvent } from "react";
import { TeacherShell } from "@/components/teacher/TeacherShell";
import { apiFetch, type ApiQuestion } from "@/lib/engagementApi";
import styles from "./page.module.css";

const tabs = [
  { id: "all", label: "Todas" },
  { id: "pending", label: "Pendentes" },
  { id: "answered", label: "Respondidas" },
] as const;

type QuestionFilter = typeof tabs[number]["id"];

export default function Duvidas() {
  const [questions, setQuestions] = useState<ApiQuestion[]>([]);
  const [filter, setFilter] = useState<QuestionFilter>("all");
  const [query, setQuery] = useState("");
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [expandedDiscussion, setExpandedDiscussion] = useState<string | null>(null);
  const [errorNotice, setErrorNotice] = useState("");

  useEffect(() => {
    let active = true;
    apiFetch<ApiQuestion[]>("/api/questions/teacher?status=all")
      .then((data) => {
        if (active) setQuestions(data);
      })
      .catch((err) => {
        if (active) {
          setErrorNotice(err instanceof Error ? `Erro ao carregar dúvidas: ${err.message}` : "Erro ao carregar dúvidas.");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const visibleQuestions = questions.filter((question) => {
    const matchesFilter = filter === "all"
      || (filter === "pending" && !question.answer)
      || (filter === "answered" && Boolean(question.answer));
    const searchableText = `${question.student_name} ${question.prompt} ${question.course_title} ${question.lesson_title}`.toLocaleLowerCase("pt-BR");
    return matchesFilter && searchableText.includes(query.toLocaleLowerCase("pt-BR"));
  });

  async function submitAnswer(event: FormEvent<HTMLFormElement>, questionId: string) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const answer = String(formData.get("answer") ?? "").trim();
    if (!answer) return;
    setErrorNotice("");

    try {
      const updated = await apiFetch<ApiQuestion>(
        `/api/questions/${encodeURIComponent(questionId)}/answer`,
        {
          method: "PATCH",
          body: JSON.stringify({ answer }),
        }
      );
      setQuestions((current) =>
        current.map((item) => (item.id === questionId ? updated : item))
      );
      setReplyingTo(null);
      setExpandedDiscussion(questionId);
    } catch (err) {
      setErrorNotice(
        err instanceof Error ? `Erro ao enviar resposta: ${err.message}` : "Erro ao enviar resposta."
      );
    }
  }

  function getTabCount(tabId: QuestionFilter) {
    if (tabId === "all") return questions.length;
    if (tabId === "pending") return questions.filter((q) => !q.answer).length;
    return questions.filter((q) => Boolean(q.answer)).length;
  }

  return (
    <TeacherShell activePage="doubts">
      <div className={styles.page}>
        <div className={styles.toolbar}>
          <div className={styles.filters} aria-label="Filtrar dúvidas">
            {tabs.map((tab) => (
              <button
                aria-pressed={filter === tab.id}
                className={`${styles.filterButton} ${filter === tab.id ? styles.filterActive : ""}`}
                key={tab.id}
                onClick={() => setFilter(tab.id)}
                type="button"
              >
                {tab.label} ({getTabCount(tab.id)})
              </button>
            ))}
          </div>
          <label className={styles.search}>
            <span aria-hidden="true" />
            <input
              aria-label="Buscar dúvidas"
              name="question-query"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar dúvidas..."
              type="search"
              value={query}
            />
          </label>
        </div>

        {errorNotice && <p role="status">{errorNotice}</p>}

        <section className={styles.questionList} aria-label="Dúvidas dos alunos" aria-live="polite">
          {visibleQuestions.map((question) => {
            const isAnswered = Boolean(question.answer);
            const initial = question.student_name.slice(0, 1).toUpperCase();
            return (
              <article className={styles.question} key={question.id}>
                <span className={styles.studentInitial} aria-hidden="true">{initial}</span>
                <div className={styles.questionContent}>
                  <div className={styles.studentLine}>
                    <h2>{question.student_name}</h2>
                    <span>{new Date(question.created_at).toLocaleDateString("pt-BR")}</span>
                  </div>
                  <p className={styles.prompt}>“{question.prompt}”</p>
                  <p className={styles.lesson}>{question.course_title} • {question.lesson_title}</p>
                  {replyingTo === question.id && (
                    <form className={styles.replyForm} onSubmit={(event) => submitAnswer(event, question.id)}>
                      <label htmlFor={`answer-${question.id}`}>Sua resposta</label>
                      <textarea autoFocus id={`answer-${question.id}`} name="answer" required rows={3} />
                      <div>
                        <button className={styles.cancelButton} onClick={() => setReplyingTo(null)} type="button">Cancelar</button>
                        <button className={styles.primaryButton} type="submit">Enviar resposta</button>
                      </div>
                    </form>
                  )}
                  {isAnswered && expandedDiscussion === question.id && (
                    <div className={styles.answer}>
                      <strong>Resposta do professor</strong>
                      <p>{question.answer}</p>
                    </div>
                  )}
                </div>
                <span className={`${styles.status} ${isAnswered ? styles.answered : styles.pending}`}>
                  {isAnswered ? "Respondida" : "Pendente"}
                </span>
                {isAnswered ? (
                  <button
                    className={styles.secondaryButton}
                    onClick={() => setExpandedDiscussion(expandedDiscussion === question.id ? null : question.id)}
                    type="button"
                  >
                    {expandedDiscussion === question.id ? "Fechar discussão" : "Ver Discussão"}
                  </button>
                ) : (
                  <button className={styles.primaryButton} onClick={() => setReplyingTo(question.id)} type="button">
                    Responder
                  </button>
                )}
              </article>
            );
          })}
          {visibleQuestions.length === 0 && <p className={styles.emptyState}>Nenhuma dúvida encontrada.</p>}
        </section>
      </div>
    </TeacherShell>
  );
}
