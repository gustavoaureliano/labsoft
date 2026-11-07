import { CheckoutFlow } from "@/components/commerce/CheckoutFlow";
import { AppShell } from "@/components/layout/AppShell";
import { catalogCourses, findCatalogCourse } from "@/data/catalog";
import { courseForCheckout } from "@/lib/api/catalogPage";
import type { SubscriptionPlan } from "@/data/subscriptionDemo";

export default async function CheckoutPage({ searchParams }: PageProps<"/checkout">) {
  const query = await searchParams;
  const courseId = typeof query.curso === "string" ? query.curso : "";
  const course = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true"
    ? await courseForCheckout(courseId) : findCatalogCourse(courseId) ?? catalogCourses[0];
  const plan: SubscriptionPlan = query.tipo === "assinatura" ? "complete" : "individual";
  return <AppShell activePage="explore"><CheckoutFlow course={course} plan={plan} /></AppShell>;
}
