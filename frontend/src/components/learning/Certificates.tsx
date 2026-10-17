"use client";

import { useState } from "react";
import Link from "next/link";
import { api, useApi, type Course } from "@/lib/api/learning";
import styles from "@/app/certificados/page.module.css";

type Certificate = {id: string; course_id: string; course_title: string; student_name: string; verification_code: string; issued_at: string; lesson_count: number};

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
  return <div><h1>Certificados</h1><p>Acompanhe suas conclusões e consulte os documentos emitidos.</p>
    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    {!certificates.data && !error && <p>Carregando certificados...</p>}
    <div className={styles.grid}>
      {certificates.data?.map(item => <article className={styles.card} key={item.id}><span className={styles.status}>Emitido</span><h2>{item.course_title}</h2><p>Concedido a {item.student_name}</p><Link href={`/certificados/${item.id}`}>Ver certificado →</Link></article>)}
      {courses.data?.filter(course => !certificates.data?.some(item => item.course_id === course.id)).map(course => <article className={styles.card} key={course.id}><span className={styles.status}>{course.completed ? "Concluído" : `Em andamento · ${course.progress}%`}</span><h2>{course.title}</h2>{course.completed ? <button type="button" disabled={busy !== null} onClick={() => void issue(course.id)}>Emitir certificado</button> : <Link href={`/meus-cursos/${course.id}`}>Continuar estudando →</Link>}</article>)}
    </div>
  </div>;
}

export function CertificateDetail({id}: {id: string}) {
  const {data, error} = useApi<Certificate>(`/api/learning/certificates/${id}`);
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Carregando certificado...</p>;
  return <div className={styles.detailPage}><Link href="/certificados">← Voltar aos certificados</Link><article className={styles.certificate}><span>AprovaAí · Emissão local de desenvolvimento</span><h1>Certificado de conclusão</h1><p>Concedido a {data.student_name} pela conclusão do curso</p><h2>{data.course_title}</h2><p>{data.lesson_count} aulas · Emitido em {new Date(data.issued_at).toLocaleDateString("pt-BR")}</p><p>Código de verificação: {data.verification_code}</p><a href={`/api/learning/certificates/${data.id}/download`}>Baixar PDF</a><p><a href={`/api/learning/certificates/verify/${data.verification_code}`} target="_blank" rel="noreferrer">Verificar certificado</a></p><small>Não é uma assinatura digital qualificada.</small></article></div>;
}
