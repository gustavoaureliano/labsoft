import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { SimpleScreen } from "@/components/ui/SimpleScreen";
import styles from "./page.module.css";

export default function CertificadosPage() {
  return (
    <AppShell activePage="certificates">
      <SimpleScreen eyebrow="Suas conquistas" title="Certificados" description="Acompanhe os cursos concluídos e os que ainda estão em andamento.">
        <div className={styles.grid}>
          <article className={styles.card}>
            <span className={styles.status}>Concluído · exemplo</span>
            <h2>Redação nota mil: da tese à conclusão</h2>
            <p>Certificado ilustrativo disponível para visualização.</p>
            <Link href="/certificados/redacao">Ver certificado →</Link>
          </article>
          <article className={styles.card}>
            <span className={styles.status}>Em andamento · 68%</span>
            <h2>Física para o ENEM: Mecânica</h2>
            <p>Continue o curso para obter o certificado quando a conclusão for registrada.</p>
            <Link href="/meus-cursos">Continuar estudando →</Link>
          </article>
        </div>
        <p className={styles.demoNote}>O certificado e o progresso são ilustrativos; a regra de emissão dependerá do backend.</p>
      </SimpleScreen>
    </AppShell>
  );
}
