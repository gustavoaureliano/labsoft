import Link from "next/link";
import type { CatalogCourse } from "@/data/catalog";
import { formatPrice } from "@/data/catalog";
import { completePlanPrice, formatSubscriptionPrice } from "@/data/subscriptionDemo";
import styles from "./Commerce.module.css";

export function PlanOptions({ course }: { course: CatalogCourse }) {
  return (
    <div className={styles.page}>
      <Link className={styles.back} href={`/cursos/${course.id}`}>← Voltar para o curso</Link>
      <header className={styles.heading}><span className={styles.eyebrow}>Formas de acesso</span><h1>Escolha como quer estudar</h1><p>Você pode adquirir somente este curso ou acessar todo o catálogo.</p></header>
      <div className={styles.plans}>
        <article className={styles.plan}>
          <span className={styles.eyebrow}>Compra individual</span>
          <h2>{course.title}</h2>
          <span className={styles.planPrice}>{formatPrice(course.price)}</span>
          <p>Pagamento único para acessar este curso.</p>
          <ul><li>Acesso ao curso escolhido</li><li>Videoaulas e materiais</li><li>Certificado ao concluir</li></ul>
          <Link className={styles.secondary} href={`/checkout?curso=${course.id}&tipo=curso`}>Escolher curso individual</Link>
        </article>
        <article className={`${styles.plan} ${styles.planFeatured}`}>
          <span className={styles.eyebrow}>Mais opções para estudar</span>
          <h2>Assinatura completa</h2>
          <span className={styles.planPrice}>{formatSubscriptionPrice(completePlanPrice)} <small>por mês</small></span>
          <p>Acesso demonstrativo a todos os cursos da plataforma.</p>
          <ul><li>Todo o catálogo</li><li>Novos cursos incluídos</li><li>Cancelamento pela área do aluno</li></ul>
          <Link className={styles.primary} href={`/checkout?curso=${course.id}&tipo=assinatura`}>Escolher assinatura</Link>
        </article>
      </div>
      <p className={styles.note}>Este é um fluxo de demonstração. Nenhuma cobrança será realizada.</p>
    </div>
  );
}
