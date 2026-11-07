"use client";

import { useState } from "react";
import Link from "next/link";
import { useAccess } from "@/lib/api/commerce";
import { isApiConfigured } from "@/lib/apiClient";
import { findCatalogCourse, formatPrice } from "@/data/catalog";
import styles from "./Commerce.module.css";

export function SubscriptionManager() {
  const [access, cancelPlan, ready, error] = useAccess();
  const [cancelError, setCancelError] = useState("");
  const [canceling, setCanceling] = useState(false);

  async function cancel() {
    setCanceling(true); setCancelError("");
    try { await cancelPlan(); }
    catch (reason) { setCancelError((reason as Error).message); }
    finally { setCanceling(false); }
  }
  if (!ready) return <p>Carregando assinatura...</p>;
  if (error) return <section role="alert"><h1>Acessos indisponíveis</h1><p>{error}</p><Link href="/perfil">Voltar ao perfil</Link></section>;

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
          <span className={styles.eyebrow}>{isApiConfigured ? "Compra individual" : "Compra demonstrativa"}</span>
          <h2>{course?.title ?? "Curso individual"}</h2>
          <p><strong>{formatPrice(subscription.price)} em pagamento único</strong></p>
          <p>Compras individuais permanecem disponíveis mesmo após cancelar uma assinatura completa.</p>
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
        <p>{pastDue ? "Não conseguimos cobrar a última mensalidade. Seu acesso está suspenso e a cobrança será tentada novamente." : "Seu acesso ao plano completo está disponível."}</p>
        {cancelError && <p role="alert">{cancelError}</p>}
        <div className={styles.actions}>
          <button className={styles.danger} type="button" disabled={canceling} onClick={() => void cancel()}>{canceling ? "Cancelando..." : "Cancelar plano"}</button>
          <Link className={styles.secondary} href="/planos">Ver outros planos</Link>
          <Link className={styles.secondary} href="/perfil">Voltar ao perfil</Link>
        </div>
      </section>
      <p className={styles.note}>Nenhuma cobrança real é realizada nesta demonstração.</p>
    </div>
  );
}
