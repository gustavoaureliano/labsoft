"use client";

import { startTransition, useCallback, useEffect, useState } from "react";
import { catalogCourses, findCatalogCourse } from "@/data/catalog";
import { completePlanPrice, type AccessDemo } from "@/data/subscriptionDemo";
import { api, jsonRequest } from "@/lib/api/learning";

// There is no auth yet: the whole prototype acts as this single user.
export const DEMO_USER_ID = 1;
// Reserved backend item_id meaning "complete plan" (whole catalog).
export const COMPLETE_PLAN_ITEM = 0;

// Backend uses integer item ids; the catalog uses string ids. Map by catalog position.
export const itemIdFor = (courseId: string) => {
  const index = catalogCourses.findIndex((course) => course.id === courseId);
  return index === -1 ? undefined : index + 1;
};
export const courseIdFor = (itemId: number) => catalogCourses[itemId - 1]?.id;

export const toCents = (reais: number) => Math.round(reais * 100);

export type PaymentMethod = "pix" | "credito" | "boleto";

type CheckoutView = { checkout_id: string; status: "processing" | "ok" | "payment_failed" };

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Payment settles asynchronously, so a purchase is: start (idempotent) then poll until it settles.
 *  Reuse the same `idempotencyKey` when retrying the same attempt; make a new one after a refusal.
 *  Resolves "ok", or "processing" if it hasn't settled within the polling window. */
export async function purchase(
  itemId: number, priceReais: number, method: PaymentMethod, plan: "one_time" | "monthly", idempotencyKey: string,
): Promise<"ok" | "processing"> {
  if (priceReais <= 0) { // free enrollment: no payment, just subscribe
    await api("/api/subscriptions", jsonRequest("POST", { user_id: DEMO_USER_ID, item_id: itemId }));
    return "ok";
  }
  const request = jsonRequest("POST", { user_id: DEMO_USER_ID, item_id: itemId, amount: toCents(priceReais), method, plan });
  let view = await api<CheckoutView>("/api/checkout", { ...request, headers: { ...request.headers, "Idempotency-Key": idempotencyKey } });
  for (let attempt = 0; view.status === "processing" && attempt < 30; attempt++) {
    await sleep(1000);
    view = await api<CheckoutView>(`/api/checkout/${view.checkout_id}`);
  }
  if (view.status === "payment_failed") throw new Error("Pagamento recusado. Tente outro método.");
  return view.status === "ok" ? "ok" : "processing";
}

export async function checkAccess(itemId: number, contentType: "video" | "resumo" = "video") {
  const query = new URLSearchParams({ user_id: String(DEMO_USER_ID), item_id: String(itemId), content_type: contentType });
  const result = await api<{ access: "allowed" | "denied" }>(`/api/access?${query}`);
  return result.access === "allowed";
}

export function sendHeartbeat(itemId: number, stamp: number) {
  void api("/api/heartbeat", jsonRequest("POST", { user_id: DEMO_USER_ID, item_id: itemId, stamp: Math.floor(stamp) })).catch(() => {});
}

// Same shape the old localStorage hook returned, now backed by the subscription service.
export function useAccess() {
  const [access, setAccess] = useState<AccessDemo>({ courseIds: [], subscription: null });
  const [ready, setReady] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const { item_ids, items } = await api<{ item_ids: number[]; items: { item_id: number; status: string }[] }>(`/api/subscriptions/${DEMO_USER_ID}`);
      const courseIds = item_ids.filter((id) => id !== COMPLETE_PLAN_ITEM).flatMap((id) => courseIdFor(id) ?? []);
      const lastCourse = courseIds.length ? findCatalogCourse(courseIds[courseIds.length - 1]) : undefined;
      const completePlan = items.find((item) => item.item_id === COMPLETE_PLAN_ITEM);
      setAccess({
        courseIds,
        subscription: completePlan && completePlan.status !== "cancelled"
          ? { plan: "complete", status: completePlan.status === "past_due" ? "past_due" : "active", price: completePlanPrice }
          : lastCourse ? { plan: "individual", status: "active", courseId: lastCourse.id, price: lastCourse.price } : null,
      });
    } catch {
      setAccess({ courseIds: [], subscription: null });
    }
    setReady(true);
  }, []);

  useEffect(() => { startTransition(() => { void refresh(); }); }, [refresh]);

  const cancelCompletePlan = useCallback(async () => {
    await api(`/api/subscriptions/${DEMO_USER_ID}/${COMPLETE_PLAN_ITEM}`, { method: "DELETE" });
    await refresh();
  }, [refresh]);

  return [access, cancelCompletePlan, ready] as const;
}
