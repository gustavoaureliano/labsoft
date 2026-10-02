"use client";

import { useState, type FormEvent } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { questionsDemoKey, type DemoQuestion } from "@/data/questionsDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./page.module.css";

type Question = {
  id: number;
  student: string;
  initial: string;
  createdAt: string;
  prompt: string;
  course: string;
  lesson: string;
  answer?: string;
};

const initialQuestions: Question[] = [
  {
    id: 1,
    student: "Lucas Oliveira",
    initial: "L",
    createdAt: "há 15 minutos",
    prompt: "Professor, no efeito fotoelétrico, por que a energia cinética dos elétrons ejetados depende apenas da frequência da luz e não da intensidade?",
    course: "Física Quântica",
    lesson: "Aula 2: Dualidade Onda-Partícula",
  },
  {
    id: 2,
    student: "Beatriz Souza",
    initial: "B",
    createdAt: "há 2 horas",
    prompt: "Tenho dúvidas sobre como a mitocôndria realiza a fosforilação oxidativa. A FUVEST costuma cobrar o papel da ATP sintase em detalhes?",
    course: "Biologia Celular",
    lesson: "Aula 4: Organelas Citoplasmáticas",
    answer: "A ATP sintase é importante, sim: entenda como o fluxo de prótons pela enzima fornece energia para produzir ATP. A prova costuma cobrar a relação entre cadeia respiratória e quimiosmose.",
  },
  {
    id: 3,
    student: "Guilherme Lima",
    initial: "G",
    createdAt: "há 1 dia",
    prompt: "Na contração muscular, qual é exatamente o papel do cálcio no retículo sarcoplasmático e como isso cai na prova paulista?",
    course: "Biologia Celular",
    lesson: "Aula 6: Citoesqueleto e Movimento",
  },
];

const tabs = [
  { id: "all", label: "Todas", count: 15 },
  { id: "pending", label: "Pendentes", count: 4 },
  { id: "answered", label: "Respondidas", count: 11 },
] as const;

type QuestionFilter = typeof tabs[number]["id"];

export default function Duvidas() {
  const [questions, setQuestions] = useState(initialQuestions);
  const [sharedQuestions, saveSharedQuestions] = useDemoStorage<DemoQuestion[]>(questionsDemoKey, []);
  const [filter, setFilter] = useState<QuestionFilter>("all");
  const [query, setQuery] = useState("");
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [expandedDiscussion, setExpandedDiscussion] = useState<number | null>(null);
  const [counts, setCounts] = useState({ all: 15, pending: 4, answered: 11 });

  const allQuestions = [...sharedQuestions.map((question) => ({ ...question, initial: question.student.slice(0, 1), createdAt: "agora" })), ...questions];
  const visibleQuestions = allQuestions.filter((question) => {
    const matchesFilter = filter === "all"
      || (filter === "pending" && !question.answer)
      || (filter === "answered" && Boolean(question.answer));
    const searchableText = `${question.student} ${question.prompt} ${question.course} ${question.lesson}`.toLocaleLowerCase("pt-BR");
    return matchesFilter && searchableText.includes(query.toLocaleLowerCase("pt-BR"));
  });

  function submitAnswer(event: FormEvent<HTMLFormElement>, questionId: number) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const answer = String(formData.get("answer") ?? "").trim();
    if (!answer) return;

    if (sharedQuestions.some((question) => question.id === questionId)) {
      saveSharedQuestions(sharedQuestions.map((question) => question.id === questionId ? { ...question, answer } : question));
    } else {
      setQuestions((current) => current.map((question) => question.id === questionId ? { ...question, answer } : question));
      setCounts((current) => ({ ...current, pending: Math.max(0, current.pending - 1), answered: current.answered + 1 }));
    }
    setReplyingTo(null);
    setExpandedDiscussion(questionId);
  }

  return (
    <AppShell activePage="doubts" account="teacher" pageTitle="Dúvidas dos Alunos" showSearch={false}>
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
                {tab.label} ({counts[tab.id] + (tab.id === "all" ? sharedQuestions.length : sharedQuestions.filter((question) => Boolean(question.answer) === (tab.id === "answered")).length)})
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

        <section className={styles.questionList} aria-label="Dúvidas dos alunos" aria-live="polite">
          {visibleQuestions.map((question) => {
            const isAnswered = Boolean(question.answer);
            return (
              <article className={styles.question} key={question.id}>
                <span className={styles.studentInitial} aria-hidden="true">{question.initial}</span>
                <div className={styles.questionContent}>
                  <div className={styles.studentLine}>
                    <h2>{question.student}</h2>
                    <span>{question.createdAt}</span>
                  </div>
                  <p className={styles.prompt}>“{question.prompt}”</p>
                  <p className={styles.lesson}>{question.course} • {question.lesson}</p>
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
    </AppShell>
  );
}
