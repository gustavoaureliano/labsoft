"use client";

import { useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import type { CatalogCourse } from "@/data/catalog";
import { formatPrice } from "@/data/catalog";
import { completePlanPrice, type SubscriptionPlan } from "@/data/subscriptionDemo";
import { COMPLETE_PLAN_ITEM, itemIdFor, purchase, type PaymentMethod } from "@/lib/api/commerce";
import { isApiConfigured } from "@/lib/apiClient";
import { useApi } from "@/lib/api/learning";
import styles from "./Commerce.module.css";

export function CheckoutFlow({ course, plan }: { course: CatalogCourse; plan: SubscriptionPlan }) {
  const [completed, setCompleted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  // One key per purchase attempt: retries/double clicks reuse it so the backend never charges twice.
  const idempotencyKey = useRef(crypto.randomUUID());
  const isComplete = plan === "complete";
  const isFree = !isComplete && course.access === "free";
  const price = isComplete ? completePlanPrice : course.price;
  const quotePath = isApiConfigured && !isFree ? `/api/checkout/quote?${new URLSearchParams(
    isComplete ? {plan:"monthly"} : {plan:"one_time",course_id:course.id})}` : null;
  const quote = useApi<{amount_cents: number}>(quotePath);
  const displayPrice = quote.data ? quote.data.amount_cents / 100 : price;

  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const itemId = isApiConfigured ? course.id : isComplete ? COMPLETE_PLAN_ITEM : itemIdFor(course.id);
    if (itemId === undefined) { setError("Curso indisponível para compra."); return; }
    if (isApiConfigured && !isFree && !quote.data) { setError(quote.error || "Não foi possível confirmar o preço no servidor."); return; }
    const method = (new FormData(event.currentTarget).get("method") as PaymentMethod | null) ?? "pix";
    setSubmitting(true);
    setError("");
    setNotice("");
    try {
      const result = await purchase(itemId, isFree ? 0 : displayPrice, method, isComplete ? "monthly" : "one_time", idempotencyKey.current);
      if (result === "ok") setCompleted(true);
      else setNotice("Seu pagamento ainda está sendo processado. Seu acesso será liberado assim que for confirmado; você pode acompanhar em Plano e assinatura.");
    } catch (e) {
      const refused = (e as Error).message.startsWith("Pagamento recusado");
      if (refused) idempotencyKey.current = crypto.randomUUID(); // a refused attempt is final; the next try is a new purchase
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
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
        <form className={styles.form} method="post" onSubmit={confirm}>
          <h2>{isFree ? "Dados da matrícula" : "Forma de pagamento"}</h2>
          <label>Nome do responsável<input name="holder" required placeholder="Nome completo" /></label>
          {!isFree && <label>Método<select name="method"><option value="pix">PIX demonstrativo</option><option value="credito">Cartão demonstrativo</option><option value="boleto">Boleto demonstrativo</option></select></label>}
          <p className={styles.note}>{isFree ? "Esta matrícula será registrada na sua conta." : "Não informe números reais de cartão. Esta tela apenas representa a etapa de contratação."}</p>
          {(error || quote.error) && <p role="alert">{error || quote.error}</p>}
          {notice && <p role="status">{notice}</p>}
          <button className={styles.button} type="submit" disabled={submitting || Boolean(quotePath && !quote.data)}>{submitting ? "Processando pagamento..." : "Confirmar acesso demonstrativo"}</button>
        </form>
        <aside className={styles.summary} aria-label="Resumo da contratação"><h2>Resumo</h2><dl><div><dt>Opção</dt><dd>{isComplete ? "Assinatura completa" : "Curso individual"}</dd></div><div><dt>Conteúdo</dt><dd>{isComplete ? "Todo o catálogo" : course.title}</dd></div><div><dt>Valor</dt><dd>{quotePath && !quote.data ? "Consultando preço..." : formatPrice(displayPrice)}{isComplete ? "/mês" : ""}</dd></div></dl></aside>
      </div>
    </div>
  );
}
