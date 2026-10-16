import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import styles from "../page.module.css";

export default function CertificadoRedacaoPage() {
  return (
    <AppShell activePage="certificates">
      <div className={styles.detailPage}>
        <Link href="/certificados">← Voltar aos certificados</Link>
        <article className={styles.certificate}>
          <span>AprovaAí · Certificado demonstrativo</span>
          <h1>Certificado de conclusão</h1>
          <p>Concedido a Bob Silva pela conclusão do curso</p>
          <h2>Redação nota mil: da tese à conclusão</h2>
          <p>Este documento é apenas uma prévia visual. Não comprova a conclusão de um curso real.</p>
        </article>
      </div>
    </AppShell>
  );
}
