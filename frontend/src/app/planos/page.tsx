import { LearningPageShell } from "@/components/layout/LearningPageShell";
import { PlanOptions } from "@/components/commerce/PlanOptions";
import { catalogCourses, findCatalogCourse } from "@/data/catalog";
import { courseForCheckout } from "@/lib/api/catalogPage";

export default async function PlansPage({ searchParams }: PageProps<"/planos">) {
  const requested = (await searchParams).curso;
  const courseId = typeof requested === "string" ? requested : "";
  const course = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true"
    ? await courseForCheckout(courseId)
    : findCatalogCourse(courseId) ?? catalogCourses.find((item) => item.access === "paid") ?? catalogCourses[0];
  return <LearningPageShell><PlanOptions course={course} /></LearningPageShell>;
}
