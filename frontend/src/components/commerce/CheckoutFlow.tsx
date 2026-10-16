"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import type { CatalogCourse } from "@/data/catalog";
import { formatPrice } from "@/data/catalog";
import { accessDemoKey, completePlanPrice, initialAccessDemo, type SubscriptionPlan } from "@/data/subscriptionDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./Commerce.module.css";

export function CheckoutFlow({ course, plan }: { course: CatalogCourse; plan: SubscriptionPlan }) {
  const [access, saveAccess] = useDemoStorage(accessDemoKey, initialAccessDemo);
  const [completed, setCompleted] = useState(false);
  const isComplete = plan === "complete";
  const isFree = !isComplete && course.access === "free";
  const price = isComplete ? completePlanPrice : course.price;

  function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveAccess({
      courseIds: isComplete ? access.courseIds : [...new Set([...access.courseIds, course.id])],
      subscription: { plan, status: "active", courseId: isComplete ? undefined : course.id, price },
    });
    setCompleted(true);
  }

  if (completed) return (
    <section className={styles.success} aria-live="polite">
      <span className={styles.eyebrow}>Acesso confirmado</span>
      <h1>Pronto para começar</h1>
      <p>{isComplete ? "Sua assinatura demonstrativa está ativa." : `${course.title} foi adicionado aos seus cursos.`}</p>
      <div className={styles.actions}><Link className={styles.primary} href="/meus-cursos">Ir para Meus Cursos</Link><Link className={styles.secondary} href={isComplete ? "/assinatura" : "/explorar-cursos"}>{isComplete ? "Gerenciar assinatura" : "Explorar outros cursos"}</Link></div>
    </section>
  );

  return (
    <div className={styles.page}>
      <Link className={styles.back} href={`/planos?curso=${course.id}`}>← Voltar para os planos</Link>
      <header className={styles.heading}><span className={styles.eyebrow}>{isFree ? "Matrícula demonstrativa" : "Checkout demonstrativo"}</span><h1>Confirme seu acesso</h1><p>{isFree ? "Confira o curso antes de adicioná-lo à sua área de estudos." : "Confira o resumo. Nenhum pagamento real será processado."}</p></header>
      <div className={styles.checkout}>
        <form className={styles.form} onSubmit={confirm}>
          <h2>{isFree ? "Dados da matrícula" : "Forma de pagamento"}</h2>
          <label>Nome do responsável<input name="holder" required placeholder="Nome completo" /></label>
          {!isFree && <label>Método<select name="method"><option>Cartão demonstrativo</option><option>PIX demonstrativo</option></select></label>}
          <p className={styles.note}>{isFree ? "Esta matrícula será salva somente neste navegador." : "Não informe números reais de cartão. Esta tela apenas representa a etapa de contratação."}</p>
          <button className={styles.button} type="submit">Confirmar acesso demonstrativo</button>
        </form>
        <aside className={styles.summary} aria-label="Resumo da contratação"><h2>Resumo</h2><dl><div><dt>Opção</dt><dd>{isComplete ? "Assinatura completa" : "Curso individual"}</dd></div><div><dt>Conteúdo</dt><dd>{isComplete ? "Todo o catálogo" : course.title}</dd></div><div><dt>Valor</dt><dd>{formatPrice(price)}{isComplete ? "/mês" : ""}</dd></div></dl></aside>
      </div>
    </div>
  );
}
