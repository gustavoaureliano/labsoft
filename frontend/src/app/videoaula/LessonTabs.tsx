"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { questionHref } from "@/data/courses";
import { initialLessonInteractions, lessonInteractionsStorageKey, lessonReportStorageKey, type LessonReport } from "@/data/lessonInteractionsDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./page.module.css";

const tabs = ["Visão Geral", "Comentários", "Anotações", "Avaliações", "Materiais"] as const;
type Tab = (typeof tabs)[number];

export function LessonTabs({ description, lessonId, lessonTitle }: { description: string; lessonId: string; lessonTitle: string }) {
  const [activeTab, setActiveTab] = useState<Tab>("Visão Geral");
  const [comment, setComment] = useState("");
  const [interactions, saveInteractions] = useDemoStorage(lessonInteractionsStorageKey(lessonId), initialLessonInteractions);
  const [report, saveReport] = useDemoStorage<LessonReport | null>(lessonReportStorageKey(lessonId), null);
  const [note, setNote] = useState<string | null>(null);

  function addComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = comment.trim();
    if (!text) return;
    saveInteractions({ ...interactions, comments: [...interactions.comments, text] });
    setComment("");
  }

  function reportLesson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const reason = String(new FormData(event.currentTarget).get("reason") ?? "").trim();
    if (reason && !report) saveReport({ reason, lessonId, lessonTitle });
  }

  return (
    <section className={styles.lessonDetails} aria-label="Detalhes da aula">
      <div className={styles.tabs} role="tablist" aria-label="Conteúdo da aula">
        {tabs.map((tab) => (
          <button
            key={tab}
            id={`tab-${tabs.indexOf(tab)}`}
            type="button"
            role="tab"
            aria-controls="lesson-tab-panel"
            aria-selected={activeTab === tab}
            className={activeTab === tab ? styles.activeTab : ""}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className={styles.tabPanel} id="lesson-tab-panel" role="tabpanel" aria-labelledby={`tab-${tabs.indexOf(activeTab)}`}>
        {activeTab === "Visão Geral" && (
          <div>
            <h2>Sobre esta aula</h2>
            <p>{description}</p>
            <form className={styles.tabForm} onSubmit={reportLesson}>
              <label htmlFor="lesson-report">Reportar problema nesta aula</label>
              <input id="lesson-report" name="reason" maxLength={160} placeholder="Descreva o problema" required disabled={Boolean(report)} />
              <button type="submit" disabled={Boolean(report)}>Enviar denúncia</button>
              {report && <p role="status">Denúncia {report.decision ? `analisada: conteúdo ${report.decision}` : "enviada para análise"} nesta demonstração.</p>}
            </form>
          </div>
        )}
        {activeTab === "Comentários" && (
          <div>
            <h2>Comentários</h2>
            <p>Os comentários são públicos para os participantes do curso e servem para compartilhar observações sobre a aula.</p>
            <div className={styles.questionCallout}>
              <span>Precisa de uma resposta do professor?</span>
              <Link href={questionHref(lessonId)}>Enviar dúvida ao professor</Link>
            </div>
            {interactions.comments.length ? (
              <ul className={styles.comments}>
                {interactions.comments.map((text, index) => <li key={`${index}-${text}`}><strong>Você</strong><p>{text}</p></li>)}
              </ul>
            ) : <p>Seja o primeiro a comentar esta aula.</p>}
            <form className={styles.tabForm} onSubmit={addComment}>
              <label htmlFor="lesson-comment">Seu comentário público</label>
              <textarea id="lesson-comment" value={comment} onChange={(event) => setComment(event.target.value)} rows={3} placeholder="Compartilhe uma observação sobre esta aula" />
              <button type="submit" disabled={!comment.trim()}>Publicar comentário</button>
            </form>
          </div>
        )}
        {activeTab === "Anotações" && (
          <div>
            <h2>Minhas anotações</h2>
            <p>Registre os pontos importantes desta aula.</p>
            <div className={styles.tabForm}>
              <label htmlFor="lesson-note">Anotação</label>
              <textarea id="lesson-note" value={note ?? interactions.note} onChange={(event) => setNote(event.target.value)} rows={5} placeholder="Escreva suas anotações" />
              <button type="button" disabled={!(note ?? interactions.note).trim()} onClick={() => saveInteractions({ ...interactions, note: (note ?? interactions.note).trim() })}>Salvar anotação</button>
              {interactions.note && <p role="status">Anotação salva neste navegador.</p>}
            </div>
          </div>
        )}
        {activeTab === "Avaliações" && (
          <div>
            <h2>Avalie esta aula</h2>
            <p>Como foi sua experiência com esta aula?</p>
            <div className={styles.rating} role="group" aria-label="Sua avaliação">
              {[1, 2, 3, 4, 5].map((value) => (
                <button key={value} type="button" aria-label={`Avaliar com ${value} ${value === 1 ? "estrela" : "estrelas"}`} aria-pressed={interactions.rating === value} onClick={() => saveInteractions({ ...interactions, rating: value })}>{value <= interactions.rating ? "★" : "☆"}</button>
              ))}
            </div>
            {interactions.rating > 0 && <p role="status">Sua avaliação: {interactions.rating} {interactions.rating === 1 ? "estrela" : "estrelas"} neste navegador.</p>}
          </div>
        )}
        {activeTab === "Materiais" && (
          <div>
            <h2>Materiais complementares</h2>
            <p>Encontre resumos e exercícios para continuar estudando.</p>
            <Link className={styles.materialLink} href="/materiais-complementares">Explorar materiais →</Link>
          </div>
        )}
      </div>
    </section>
  );
}
