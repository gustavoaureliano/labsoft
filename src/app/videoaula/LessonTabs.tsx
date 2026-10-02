"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import styles from "./page.module.css";

const tabs = ["Visão Geral", "Comentários", "Anotações", "Avaliações", "Materiais"] as const;
type Tab = (typeof tabs)[number];

export function LessonTabs({ description }: { description: string }) {
  const [activeTab, setActiveTab] = useState<Tab>("Visão Geral");
  const [comment, setComment] = useState("");
  const [comments, setComments] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [savedNote, setSavedNote] = useState("");
  const [rating, setRating] = useState(0);

  function addComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = comment.trim();
    if (!text) return;
    setComments((previous) => [...previous, text]);
    setComment("");
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
          </div>
        )}
        {activeTab === "Comentários" && (
          <div>
            <h2>Comentários</h2>
            {comments.length ? (
              <ul className={styles.comments}>
                {comments.map((text, index) => <li key={`${index}-${text}`}><strong>Você</strong><p>{text}</p></li>)}
              </ul>
            ) : <p>Seja o primeiro a comentar esta aula.</p>}
            <form className={styles.tabForm} onSubmit={addComment}>
              <label htmlFor="lesson-comment">Seu comentário</label>
              <textarea id="lesson-comment" value={comment} onChange={(event) => setComment(event.target.value)} rows={3} placeholder="Escreva uma dúvida ou observação" />
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
              <textarea id="lesson-note" value={note} onChange={(event) => setNote(event.target.value)} rows={5} placeholder="Escreva suas anotações" />
              <button type="button" disabled={!note.trim()} onClick={() => setSavedNote(note.trim())}>Salvar anotação</button>
              {savedNote && <p role="status">Anotação salva nesta sessão.</p>}
            </div>
          </div>
        )}
        {activeTab === "Avaliações" && (
          <div>
            <h2>Avalie esta aula</h2>
            <p>Como foi sua experiência com esta aula?</p>
            <div className={styles.rating} role="group" aria-label="Sua avaliação">
              {[1, 2, 3, 4, 5].map((value) => (
                <button key={value} type="button" aria-label={`Avaliar com ${value} ${value === 1 ? "estrela" : "estrelas"}`} aria-pressed={rating === value} onClick={() => setRating(value)}>{value <= rating ? "★" : "☆"}</button>
              ))}
            </div>
            {rating > 0 && <p role="status">Sua avaliação: {rating} {rating === 1 ? "estrela" : "estrelas"} nesta sessão.</p>}
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
