"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { api, jsonRequest, useApi } from "@/lib/api/learning";
import { ApiError, fetchMyReportStatus, sendReport, type ApiComment, type ApiMyReportStatus, type ApiReportItemType } from "@/lib/engagementApi";
import styles from "./page.module.css";

type Note = {content: string};
type Comment = Pick<ApiComment, "id" | "author_name" | "content" | "created_at">;
type Rating = {student_stars: number | null; average_rating: number; total_ratings: number};
const tabs = ["Visão Geral", "Comentários", "Anotações", "Avaliações", "Materiais"] as const;

export function RealLessonTabs({description, lessonId, courseId}: {description: string; lessonId: string; courseId: string}) {
  const [active, setActive] = useState<(typeof tabs)[number]>("Visão Geral");
  const [comment, setComment] = useState("");
  const [noteDraft, setNoteDraft] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const base = `/api/interactions/lessons/${encodeURIComponent(lessonId)}`;
  const comments = useApi<Comment[]>(active === "Comentários" ? `${base}/comments?revision=${revision}` : null);
  const note = useApi<Note>(active === "Anotações" ? `${base}/note?revision=${revision}` : null);
  const rating = useApi<Rating>(active === "Avaliações" ? `/api/interactions/ratings/${encodeURIComponent(lessonId)}?target_type=lesson&revision=${revision}` : null);

  const [reportingComment, setReportingComment] = useState<string | null>(null);

  async function act<T>(operation: () => Promise<T>, success: string | ((result: T) => string)) {
    if (busy) return;
    setBusy(true); setMessage("");
    try {
      const result = await operation();
      setMessage(typeof success === "function" ? success(result) : success);
      setRevision(current => current + 1);
    } catch (error) {
      setMessage(`Não foi possível salvar: ${(error as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  function submitComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = comment.trim();
    if (!content) return;
    void act(async () => {
      const created = await api<ApiComment>(`${base}/comments`, jsonRequest("POST", {content}));
      setComment("");
      return created;
    }, created => created.moderation_status === "held"
      ? "Comentário enviado para moderação; ele aparecerá após revisão."
      : "Comentário enviado.");
  }

  return <section className={styles.lessonDetails} aria-label="Detalhes da aula">
    <div className={styles.tabs} role="tablist" aria-label="Conteúdo da aula">
      {tabs.map((tab, index) => <button key={tab} id={`tab-${index}`} type="button" role="tab" aria-controls="lesson-tab-panel"
        aria-selected={active === tab} className={active === tab ? styles.activeTab : ""}
        onClick={() => {setActive(tab); setMessage("");}}>{tab}</button>)}
    </div>
    <div className={styles.tabPanel} id="lesson-tab-panel" role="tabpanel" aria-labelledby={`tab-${tabs.indexOf(active)}`}>
      {active === "Visão Geral" && <><h2>Sobre esta aula</h2><p>{description}</p>
        <ReportControl itemType="lesson" itemId={lessonId} label="Reportar problema nesta aula" /></>}
      {active === "Comentários" && <>
        <h2>Comentários</h2>
        <Link href={`/duvidas?${new URLSearchParams({curso:courseId,aula:lessonId})}`}>Enviar dúvida ao professor</Link>
        {comments.error ? <p role="alert">{comments.error}</p> : !comments.data ? <p role="status">Carregando comentários...</p> :
          comments.data.length ? <ul className={styles.comments}>{comments.data.map(item => <li key={item.id}>
            <div className={styles.commentMeta}><strong>{item.author_name}</strong><time dateTime={item.created_at}>{formatDateTime(item.created_at)}</time></div>
            <p>{item.content}</p>
            <button type="button" className={styles.commentReportButton} aria-expanded={reportingComment === item.id}
              onClick={() => setReportingComment(current => current === item.id ? null : item.id)}>Denunciar</button>
            {reportingComment === item.id && <ReportControl itemType="comment" itemId={item.id} label="Motivo da denúncia do comentário" />}
          </li>)}</ul> : <p>Seja o primeiro a comentar esta aula.</p>}
        <form className={styles.tabForm} onSubmit={submitComment}><label htmlFor="lesson-comment">Seu comentário público</label>
          <textarea id="lesson-comment" value={comment} onChange={event => setComment(event.target.value)} rows={3} maxLength={2000} />
          <button type="submit" disabled={busy || !comment.trim()}>Publicar comentário</button></form>
      </>}
      {active === "Anotações" && <><h2>Minhas anotações</h2>
        {note.error ? <p role="alert">{note.error}</p> : !note.data ? <p role="status">Carregando anotação...</p> :
          <div className={styles.tabForm}><label htmlFor="lesson-note">Anotação privada</label>
            <textarea id="lesson-note" value={noteDraft ?? note.data.content} onChange={event => setNoteDraft(event.target.value)} rows={5} maxLength={5000} />
            <button type="button" disabled={busy || !(noteDraft ?? note.data.content).trim()} onClick={() => void act(async () => {
              await api(`${base}/note`, jsonRequest("PUT", {content:(noteDraft ?? note.data?.content ?? "").trim()}));
              setNoteDraft(null);
            }, "Anotação salva.")}>Salvar anotação</button></div>}
      </>}
      {active === "Avaliações" && <><h2>Avalie esta aula</h2>
        {rating.error ? <p role="alert">{rating.error}</p> : !rating.data ? <p role="status">Carregando avaliação...</p> :
          <div className={styles.rating} role="group" aria-label="Sua avaliação">
            {[1,2,3,4,5].map(stars => <button key={stars} type="button" disabled={busy} aria-label={`Avaliar com ${stars} ${stars === 1 ? "estrela" : "estrelas"}`}
              aria-pressed={rating.data?.student_stars === stars} onClick={() => void act(() => api(`/api/interactions/ratings/${encodeURIComponent(lessonId)}`,
                jsonRequest("PUT", {target_type:"lesson",stars})), "Avaliação salva.")}>{stars <= (rating.data?.student_stars ?? 0) ? "★" : "☆"}</button>)}
            <p>Média: {rating.data.average_rating} ({rating.data.total_ratings} avaliações)</p>
          </div>}
      </>}
      {active === "Materiais" && <><h2>Materiais complementares</h2><Link href={`/materiais-complementares?curso=${encodeURIComponent(courseId)}&aula=${encodeURIComponent(lessonId)}`}>Ver materiais desta aula</Link></>}
      {message && <p role="status">{message}</p>}
    </div>
  </section>;
}

function formatDateTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("pt-BR", {dateStyle: "short", timeStyle: "short"});
}

function reportStatusText(report: ApiMyReportStatus) {
  if (report.status === "resolved") return `Denúncia analisada pela moderação: conteúdo ${report.decision ?? "revisado"}.`;
  return "Denúncia enviada; aguardando análise da moderação.";
}

function ReportControl({itemType, itemId, label}: {itemType: ApiReportItemType; itemId: string; label: string}) {
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState<{key: string; report?: ApiMyReportStatus; error?: string} | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const key = `${itemType}:${itemId}:${revision}`;
  const inputId = `report-${itemType}-${itemId}`;

  useEffect(() => {
    let active = true;
    fetchMyReportStatus(itemType, itemId).then(
      report => { if (active) setResult({key, report}); },
      error => { if (active) setResult({key, error: (error as Error).message}); },
    );
    return () => { active = false; };
  }, [itemType, itemId, key]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = reason.trim();
    if (!text || busy) return;
    setBusy(true); setMessage("");
    try {
      await sendReport(itemType, itemId, text);
      setReason("");
      setMessage("Denúncia enviada para análise da moderação.");
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) setMessage("Você já denunciou este conteúdo.");
      else if (error instanceof ApiError && error.status === 404) setMessage("Conteúdo não encontrado; ele pode ter sido removido.");
      else setMessage(`Não foi possível enviar a denúncia: ${(error as Error).message}`);
    } finally {
      setBusy(false);
      setRevision(current => current + 1);
    }
  }

  const current = result?.key === key ? result : null;
  return <div>
    {!current ? <p role="status">Consultando denúncia...</p>
      : current.error ? <p role="alert">Não foi possível consultar a denúncia: {current.error}</p>
      : current.report?.reported ? <p role="status">{reportStatusText(current.report)}{current.report.reason ? ` Motivo: ${current.report.reason}` : ""}</p>
      : <form className={styles.tabForm} onSubmit={submit}>
        <label htmlFor={inputId}>{label}</label>
        <input id={inputId} value={reason} onChange={event => setReason(event.target.value)} maxLength={500} placeholder="Descreva o problema" required />
        <button type="submit" disabled={busy || !reason.trim()}>Enviar denúncia</button>
      </form>}
    {message && <p role="status">{message}</p>}
  </div>;
}
