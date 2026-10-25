"use client";

import { useState } from "react";
import Link from "next/link";
import { api, useApi, type Course } from "@/lib/api/learning";
import styles from "@/app/certificados/page.module.css";

type Certificate = {id: string; course_id: string; course_title: string; student_name: string; verification_code: string; issued_at: string; lesson_count: number; workload_seconds: number};

function CertificateCard({ item }: { item: Certificate }) {
  return <article className={styles.card}>
    <Link className={styles.cardLink} href={`/certificados/${item.id}`} aria-label={`Ver certificado de ${item.course_title}`}>
      <span className={styles.status}>Emitido</span>
      <h3>{item.course_title}</h3>
      <p>Concedido a {item.student_name} em {new Date(item.issued_at).toLocaleDateString("pt-BR")}</p>
      <span className={styles.cardAction}>Ver certificado →</span>
    </Link>
  </article>;
}

function CourseCertificateCard({ course, busy, onIssue }: { course: Course; busy: boolean; onIssue: (id: string) => void }) {
  const restricted = course.access_status !== "active";
  const href = restricted ? `/cursos/${course.id}` : `/meus-cursos/${course.id}`;
  const status = restricted ? course.access_status === "expired" ? "Acesso expirado" : "Acesso bloqueado" : course.completed ? "Pronto para emitir" : `Em andamento · ${course.progress}%`;
  const description = restricted ? "Aulas indisponíveis enquanto o acesso estiver restrito." : course.completed ? `${course.total_lessons} aulas concluídas` : `${course.completed_lessons} de ${course.total_lessons} aulas concluídas`;
  const action = restricted ? "Ver detalhes do acesso →" : course.completed ? "Emitir certificado →" : "Continuar estudando →";

  return <article className={styles.card}>
    <span className={styles.status}>{status}</span>
    <h3>{course.title}</h3>
    <p>{description}</p>
    <span className={styles.cardAction}>{action}</span>
    {course.completed && !restricted ? <button className={styles.cardButton} type="button" disabled={busy} aria-label={`Emitir certificado de ${course.title}`} onClick={() => onIssue(course.id)} />
      : <Link className={styles.cardOverlay} href={href} aria-label={`${restricted ? "Ver detalhes do acesso a" : "Continuar"} ${course.title}`} />}
  </article>;
}

export function Certificates() {
  const [version, setVersion] = useState(0);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const courses = useApi<Course[]>("/api/learning/courses");
  const certificates = useApi<Certificate[]>(`/api/learning/certificates?v=${version}`);
  async function issue(courseId: string) {
    if (busy) return;
    setBusy(courseId); setNotice("");
    try { await api(`/api/learning/courses/${courseId}/certificate`, {method: "POST"}); setVersion(value => value + 1); setNotice("Certificado emitido."); }
    catch (error) {setNotice((error as Error).message);}
    finally {setBusy(null);}
  }
  const error = courses.error || certificates.error;
  const issued = certificates.data ?? [];
  const pending = courses.data?.filter(course => !issued.some(item => item.course_id === course.id)) ?? [];
  const ready = pending.filter(course => course.access_status === "active" && course.completed);
  const studying = pending.filter(course => course.access_status === "active" && !course.completed);
  const restricted = pending.filter(course => course.access_status !== "active");
  return <div><h1>Certificados</h1><p>Acompanhe suas conclusões e consulte os documentos emitidos.</p>
    {error && <p role="alert">{error}</p>}{notice && <p role={notice === "Certificado emitido." ? "status" : "alert"}>{notice}</p>}
    {!certificates.data && !error && <p>Carregando certificados...</p>}
    {certificates.data && <section className={styles.group} aria-labelledby="issued-title"><h2 id="issued-title">Emitidos</h2>
      {issued.length ? <div className={styles.grid}>{issued.map(item => <CertificateCard key={item.id} item={item} />)}</div> : <p>Você ainda não emitiu certificados.</p>}
    </section>}
    {courses.data && certificates.data && <>
      <section className={styles.group} aria-labelledby="ready-title"><h2 id="ready-title">Prontos para emitir</h2>
        {ready.length ? <div className={styles.grid}>{ready.map(course => <CourseCertificateCard key={course.id} course={course} busy={busy !== null} onIssue={issue} />)}</div> : <p>Nenhum curso concluído aguardando emissão.</p>}
      </section>
      {studying.length > 0 && <section className={styles.group} aria-labelledby="studying-title"><h2 id="studying-title">Em andamento</h2><div className={styles.grid}>{studying.map(course => <CourseCertificateCard key={course.id} course={course} busy={false} onIssue={issue} />)}</div></section>}
      {restricted.length > 0 && <section className={styles.group} aria-labelledby="restricted-title"><h2 id="restricted-title">Acesso indisponível</h2><div className={styles.grid}>{restricted.map(course => <CourseCertificateCard key={course.id} course={course} busy={false} onIssue={issue} />)}</div></section>}
    </>}
  </div>;
}

export function CertificateDetail({id}: {id: string}) {
  const {data, error} = useApi<Certificate>(`/api/learning/certificates/${id}`);
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Carregando certificado...</p>;
  return <div className={styles.detailPage}><Link href="/certificados">← Voltar aos certificados</Link><article className={styles.certificate}><span>AprovaAí · Emissão local de desenvolvimento</span><h1>Certificado de conclusão</h1><p>Concedido a {data.student_name} pela conclusão do curso</p><h2>{data.course_title}</h2><p>{data.lesson_count} aulas · Emitido em {new Date(data.issued_at).toLocaleDateString("pt-BR")}</p><p>Código de verificação: {data.verification_code}</p><a href={`/api/learning/certificates/${data.id}/download`}>Baixar PDF</a><p><a href={`/api/learning/certificates/verify/${data.verification_code}`} target="_blank" rel="noreferrer">Verificar certificado</a></p><small>Não é uma assinatura digital qualificada.</small></article></div>;
}
