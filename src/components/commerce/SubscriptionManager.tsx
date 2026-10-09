"use client";

import Link from "next/link";
import { accessDemoKey, initialAccessDemo } from "@/data/subscriptionDemo";
import { findCatalogCourse, formatPrice } from "@/data/catalog";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./Commerce.module.css";

export function SubscriptionManager() {
  const [access, saveAccess, ready] = useDemoStorage(accessDemoKey, initialAccessDemo);
  if (!ready) return <p>Carregando assinatura...</p>;

  const subscription = access.subscription;
  if (!subscription) return (
    <div className={styles.page}>
      <header className={styles.heading}><span className={styles.eyebrow}>Sua conta</span><h1>Plano e assinatura</h1><p>Você ainda não contratou um plano nesta demonstração.</p></header>
      <div className={styles.actions}><Link className={styles.primary} href="/planos">Conhecer planos</Link><Link className={styles.secondary} href="/perfil">Voltar ao perfil</Link></div>
    </div>
  );

  const active = subscription.status === "active";
  if (subscription.plan === "individual") {
    const course = subscription.courseId ? findCatalogCourse(subscription.courseId) : undefined;
    return (
      <div className={styles.page}>
        <header className={styles.heading}><span className={styles.eyebrow}>Sua conta</span><h1>Acesso individual</h1><p>Este acesso foi registrado somente neste navegador.</p></header>
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

  return (
    <div className={styles.page}>
      <header className={styles.heading}><span className={styles.eyebrow}>Sua conta</span><h1>Plano e assinatura</h1><p>Acompanhe a forma de acesso salva neste navegador.</p></header>
      <section className={styles.section}>
        <span className={styles.eyebrow}>{active ? "Ativo" : "Cancelado"}</span>
        <h2>Assinatura completa</h2>
        <p><strong>{formatPrice(subscription.price)} por mês</strong></p>
        <p>{active ? "Seu acesso demonstrativo está disponível." : "O plano foi cancelado nesta demonstração. Você pode reativá-lo a qualquer momento."}</p>
        <div className={styles.actions}>
          <button className={active ? styles.danger : styles.primary} type="button" onClick={() => saveAccess({ ...access, subscription: { ...subscription, status: active ? "cancelled" : "active" } })}>{active ? "Cancelar plano" : "Reativar plano"}</button>
          <Link className={styles.secondary} href="/planos">Ver outros planos</Link>
          <Link className={styles.secondary} href="/perfil">Voltar ao perfil</Link>
        </div>
      </section>
      <p className={styles.note}>Alterações feitas aqui são apenas locais e não realizam cobranças.</p>
    </div>
  );
}
