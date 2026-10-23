"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { questionHref } from "@/data/courses";
import {
  apiFetch,
  type ApiComment,
  type ApiMyReportStatus,
  type ApiRatingSummary,
} from "@/lib/engagementApi";
import styles from "./page.module.css";

const tabs = ["Visão Geral", "Comentários", "Anotações", "Avaliações", "Materiais"] as const;
type Tab = (typeof tabs)[number];

export function LessonTabs({ description, lessonId }: { description: string; lessonId: string; lessonTitle: string }) {
  const [activeTab, setActiveTab] = useState<Tab>("Visão Geral");
  const [comment, setComment] = useState("");
  const [comments, setComments] = useState<ApiComment[]>([]);
  const [commentNotice, setCommentNotice] = useState("");
  const [note, setNote] = useState("");
  const [noteSavedStatus, setNoteSavedStatus] = useState("");
  const [ratingSummary, setRatingSummary] = useState<ApiRatingSummary | null>(null);
  const [ratingNotice, setRatingNotice] = useState("");
  const [reportStatus, setReportStatus] = useState<ApiMyReportStatus | null>(null);
  const [reportNotice, setReportNotice] = useState("");

  useEffect(() => {
    let active = true;
    async function loadFromBackend() {
      try {
        const [noteData, commentsData, ratingData, myReport] = await Promise.all([
          apiFetch<{ content: string }>(
            `/api/interactions/lessons/${encodeURIComponent(lessonId)}/note`
          ),
          apiFetch<ApiComment[]>(
            `/api/interactions/lessons/${encodeURIComponent(lessonId)}/comments`
          ),
          apiFetch<ApiRatingSummary>(
            `/api/interactions/ratings/${encodeURIComponent(lessonId)}?target_type=lesson`
          ),
          apiFetch<ApiMyReportStatus>(
            `/api/moderation/reports/my/lesson/${encodeURIComponent(lessonId)}`
          ),
        ]);
        if (!active) return;
        setNote(noteData.content ?? "");
        if (noteData.content) {
          setNoteSavedStatus("Anotação salva neste navegador.");
        }
        setComments(commentsData);
        setRatingSummary(ratingData);
        setReportStatus(myReport);
      } catch (err) {
        if (!active) return;
        const msg = err instanceof Error ? err.message : "Erro ao carregar dados da aula.";
        setCommentNotice(msg);
      }
    }
    void loadFromBackend();
    return () => {
      active = false;
    };
  }, [lessonId]);

  async function addComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = comment.trim();
    if (!text) return;
    setCommentNotice("");
    try {
      const created = await apiFetch<ApiComment>(
        `/api/interactions/lessons/${encodeURIComponent(lessonId)}/comments`,
        {
          method: "POST",
          body: JSON.stringify({ content: text }),
        }
      );
      setComment("");
      if (created.moderation_status === "held") {
        setCommentNotice("Seu comentário foi retido para análise da moderação.");
      } else {
        setComments((prev) => [...prev, created]);
      }
    } catch (err) {
      setCommentNotice(
        err instanceof Error ? `Erro ao publicar comentário: ${err.message}` : "Erro ao publicar comentário."
      );
    }
  }

  async function saveNote() {
    const content = note.trim();
    if (!content) return;
    setNoteSavedStatus("");
    try {
      const saved = await apiFetch<{ content: string }>(
        `/api/interactions/lessons/${encodeURIComponent(lessonId)}/note`,
        {
          method: "PUT",
          body: JSON.stringify({ content }),
        }
      );
      setNote(saved.content);
      setNoteSavedStatus("Anotação salva neste navegador.");
    } catch (err) {
      setNoteSavedStatus(
        err instanceof Error ? `Erro ao salvar anotação: ${err.message}` : "Erro ao salvar anotação."
      );
    }
  }

  async function submitRating(stars: number) {
    setRatingNotice("");
    try {
      const summary = await apiFetch<ApiRatingSummary>(
        `/api/interactions/ratings/${encodeURIComponent(lessonId)}`,
        {
          method: "PUT",
          body: JSON.stringify({ target_type: "lesson", stars }),
        }
      );
      setRatingSummary(summary);
    } catch (err) {
      setRatingNotice(
        err instanceof Error ? `Erro ao registrar avaliação: ${err.message}` : "Erro ao registrar avaliação."
      );
    }
  }

  async function reportLesson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const reason = String(new FormData(form).get("reason") ?? "").trim();
    if (!reason || reportStatus?.reported) return;
    setReportNotice("");
    try {
      await apiFetch("/api/moderation/reports", {
        method: "POST",
        body: JSON.stringify({ item_id: lessonId, item_type: "lesson", reason }),
      });
      setReportStatus({ reported: true, reason, status: "pending", decision: null });
    } catch (err) {
      setReportNotice(
        err instanceof Error ? `Erro ao enviar denúncia: ${err.message}` : "Erro ao enviar denúncia."
      );
    }
  }

  const activeRating = ratingSummary?.student_stars ?? 0;
  const isReported = Boolean(reportStatus?.reported);

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
              <input id="lesson-report" name="reason" maxLength={160} placeholder="Descreva o problema" required disabled={isReported} />
              <button type="submit" disabled={isReported}>Enviar denúncia</button>
              {isReported && (
                <p role="status">
                  Denúncia {reportStatus?.decision ? `analisada: conteúdo ${reportStatus.decision}` : "enviada para análise"} nesta demonstração.
                </p>
              )}
              {reportNotice && <p role="status">{reportNotice}</p>}
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
            {comments.length ? (
              <ul className={styles.comments}>
                {comments.map((item) => <li key={item.id}><strong>{item.author_name}</strong><p>{item.content}</p></li>)}
              </ul>
            ) : <p>Seja o primeiro a comentar esta aula.</p>}
            {commentNotice && <p role="status">{commentNotice}</p>}
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
              <textarea id="lesson-note" value={note} onChange={(event) => setNote(event.target.value)} rows={5} placeholder="Escreva suas anotações" />
              <button type="button" disabled={!note.trim()} onClick={saveNote}>Salvar anotação</button>
              {noteSavedStatus && <p role="status">{noteSavedStatus}</p>}
            </div>
          </div>
        )}
        {activeTab === "Avaliações" && (
          <div>
            <h2>Avalie esta aula</h2>
            <p>Como foi sua experiência com esta aula?</p>
            <div className={styles.rating} role="group" aria-label="Sua avaliação">
              {[1, 2, 3, 4, 5].map((value) => (
                <button key={value} type="button" aria-label={`Avaliar com ${value} ${value === 1 ? "estrela" : "estrelas"}`} aria-pressed={activeRating === value} onClick={() => submitRating(value)}>{value <= activeRating ? "★" : "☆"}</button>
              ))}
            </div>
            {activeRating > 0 && (
              <p role="status">
                Sua avaliação: {activeRating} {activeRating === 1 ? "estrela" : "estrelas"} neste navegador.
              </p>
            )}
            {ratingNotice && <p role="status">{ratingNotice}</p>}
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
