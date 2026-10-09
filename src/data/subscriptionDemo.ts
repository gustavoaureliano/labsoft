export type SubscriptionPlan = "individual" | "complete";
export type SubscriptionStatus = "active" | "cancelled";

export type AccessDemo = {
  courseIds: string[];
  subscription: null | { plan: SubscriptionPlan; status: SubscriptionStatus; courseId?: string; price: number };
};

export const accessDemoKey = "aprovaai-access-demo";
export const initialAccessDemo: AccessDemo = { courseIds: [], subscription: null };
export const completePlanPrice = 49.9;

export function formatSubscriptionPrice(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}
