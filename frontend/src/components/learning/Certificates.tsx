"use client";

import { useState } from "react";
import Link from "next/link";
import { api, useApi, type Course } from "@/lib/api/learning";
import styles from "@/app/certificados/page.module.css";

type Certificate = {id: string; course_id: string; course_title: string; student_name: string; verification_code: string; issued_at: string; lesson_count: number; workload_seconds: number};
type PublicCertificate = Pick<Certificate, "student_name" | "course_title" | "issued_at" | "verification_code">;

function durationLabel(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.round(seconds % 60);
  return `${minutes} min${remaining ? ` ${remaining} s` : ""}`;
}

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
  if (error) return <p role="alert">{error} <Link href="/certificados">Voltar aos certificados</Link></p>;
  if (!data) return <p>Carregando certificado...</p>;
  return <div className={styles.detailPage}>
    <Link className={styles.backLink} href="/certificados">← Voltar aos certificados</Link>
    <article className={styles.certificate}>
      <span className={styles.eyebrow}>AprovaAí · Emissão local de desenvolvimento</span>
      <h1>Certificado de conclusão</h1>
      <p>Registramos que <strong>{data.student_name}</strong> concluiu o curso</p>
      <h2>{data.course_title}</h2>
      <dl className={styles.metadata}>
        <div><dt>Aulas na emissão</dt><dd>{data.lesson_count}</dd></div>
        <div><dt>Duração dos vídeos na emissão</dt><dd>{durationLabel(data.workload_seconds)}</dd></div>
        <div><dt>Emitido em</dt><dd>{new Date(data.issued_at).toLocaleDateString("pt-BR")}</dd></div>
      </dl>
      <p className={styles.code}>Código de verificação <strong>{data.verification_code}</strong></p>
      <p className={styles.disclaimer}>Emissão local de desenvolvimento; não constitui assinatura digital qualificada nem comprovação de horas assistidas.</p>
    </article>
    <div className={styles.detailActions}>
      <a className={styles.primaryAction} href={`/api/learning/certificates/${data.id}/download`}>Baixar PDF</a>
      <Link className={styles.secondaryAction} href={`/certificados/verificar/${encodeURIComponent(data.verification_code)}`} target="_blank" rel="noreferrer">Verificar certificado</Link>
    </div>
  </div>;
}

export function CertificateVerification({code}: {code: string}) {
  const {data, error} = useApi<PublicCertificate>(`/api/learning/certificates/verify/${encodeURIComponent(code)}`);
  if (error) {
    const missing = /não encontrado|404/i.test(error);
    return <section className={styles.verification} role="alert"><h1>{missing ? "Certificado não encontrado" : "Não foi possível verificar o certificado"}</h1><p>{missing ? "Não encontramos um registro com este código. Confira o endereço recebido." : "A consulta está indisponível no momento. Tente novamente mais tarde."}</p><Link className={styles.backLink} href="/">Voltar ao início</Link></section>;
  }
  if (!data) return <p role="status">Consultando certificado...</p>;
  return <section className={styles.verification}>
    <span className={styles.eyebrow}>AprovaAí · Verificação de certificado</span>
    <h1>Registro de emissão encontrado</h1>
    <p>Este código corresponde a um certificado de conclusão emitido localmente.</p>
    <dl className={styles.metadata}>
      <div><dt>Nome registrado</dt><dd>{data.student_name}</dd></div>
      <div><dt>Curso</dt><dd>{data.course_title}</dd></div>
      <div><dt>Data de emissão</dt><dd>{new Date(data.issued_at).toLocaleDateString("pt-BR")}</dd></div>
    </dl>
    <p className={styles.code}>Código de verificação <strong>{data.verification_code}</strong></p>
    <p className={styles.disclaimer}>Esta consulta confirma apenas a existência do registro neste protótipo. Não é uma assinatura digital qualificada nem uma verificação de identidade.</p>
    <Link className={styles.backLink} href="/">Voltar ao início</Link>
  </section>;
}
