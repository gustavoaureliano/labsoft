"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import styles from "@/app/certificados/page.module.css";

export function CertificateCodeForm() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = code.trim().toLowerCase();
    if (!/^[0-9a-f]{32}$/.test(normalized)) {
      setError("Informe o código de 32 caracteres impresso no certificado.");
      return;
    }
    setError("");
    router.push(`/certificados/verificar/${normalized}`);
  }

  return <section className={styles.verification}>
    <span className={styles.eyebrow}>AprovaAí · Consulta pública</span>
    <h1>Verificar certificado</h1>
    <p>Digite o código de verificação que aparece no certificado ou no PDF recebido. Não é necessário entrar na plataforma.</p>
    <form className={styles.verificationForm} onSubmit={submit}>
      <label htmlFor="certificate-code">Código de verificação</label>
      <input id="certificate-code" name="code" value={code} onChange={event => { setCode(event.target.value); setError(""); }} maxLength={64} autoComplete="off" spellCheck={false} placeholder="Cole os 32 caracteres do certificado" aria-invalid={Boolean(error)} aria-describedby={error ? "certificate-code-error" : undefined} />
      {error && <p id="certificate-code-error" role="alert">{error}</p>}
      <button type="submit" disabled={!code.trim()}>Consultar registro</button>
    </form>
    <p className={styles.disclaimer}>A consulta confirma somente a existência do registro de emissão neste protótipo. Não valida a autenticidade do arquivo PDF nem substitui uma assinatura digital qualificada.</p>
  </section>;
}
