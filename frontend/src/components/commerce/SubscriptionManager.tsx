"use client";

import Link from "next/link";
import { useAccess } from "@/lib/api/commerce";
import { findCatalogCourse, formatPrice } from "@/data/catalog";
import styles from "./Commerce.module.css";

export function SubscriptionManager() {
  const [access, cancelPlan, ready] = useAccess();
  if (!ready) return <p>Carregando assinatura...</p>;

  const subscription = access.subscription;
  if (!subscription) return (
    <div className={styles.page}>
      <header className={styles.heading}><span className={styles.eyebrow}>Sua conta</span><h1>Plano e assinatura</h1><p>Você não tem um plano ativo. Cancelamentos liberam o acesso imediatamente.</p></header>
      <div className={styles.actions}><Link className={styles.primary} href="/planos">Conhecer planos</Link><Link className={styles.secondary} href="/perfil">Voltar ao perfil</Link></div>
    </div>
  );

  if (subscription.plan === "individual") {
    const course = subscription.courseId ? findCatalogCourse(subscription.courseId) : undefined;
    return (
      <div className={styles.page}>
        <header className={styles.heading}><span className={styles.eyebrow}>Sua conta</span><h1>Acesso individual</h1><p>Este acesso está registrado na sua conta.</p></header>
        <section className={styles.section}>
          <span className={styles.eyebrow}>Compra demonstrativa</span>
          <h2>{course?.title ?? "Curso individual"}</h2>
          <p><strong>{formatPrice(subscription.price)} em pagamento único</strong></p>
          <p>Compras individuais não são tratadas como assinaturas e não possuem cancelamento nesta demonstração.</p>
          <div className={styles.actions}><Link className={styles.primary} href="/meus-cursos">Ir para Meus Cursos</Link><Link className={styles.secondary} href="/planos">Ver outras opções</Link><Link className={styles.secondary} href="/perfil">Voltar ao perfil</Link></div>
        </section>
      </div>
    );
  }

  const pastDue = subscription.status === "past_due";
  return (
    <div className={styles.page}>
      <header className={styles.heading}><span className={styles.eyebrow}>Sua conta</span><h1>Plano e assinatura</h1><p>Acompanhe a forma de acesso da sua conta.</p></header>
      <section className={styles.section}>
        <span className={styles.eyebrow}>{pastDue ? "Pagamento pendente" : "Ativo"}</span>
        <h2>Assinatura completa</h2>
        <p><strong>{formatPrice(subscription.price)} por mês</strong></p>
        <p>{pastDue ? "Não conseguimos cobrar a última mensalidade. Seu acesso está suspenso e a cobrança será tentada novamente." : "Seu acesso demonstrativo está disponível."}</p>
        <div className={styles.actions}>
          <button className={styles.danger} type="button" onClick={() => void cancelPlan()}>Cancelar plano</button>
          <Link className={styles.secondary} href="/planos">Ver outros planos</Link>
          <Link className={styles.secondary} href="/perfil">Voltar ao perfil</Link>
        </div>
      </section>
      <p className={styles.note}>Nenhuma cobrança real é realizada nesta demonstração.</p>
    </div>
  );
}
