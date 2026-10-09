import { LearningPageShell } from "@/components/layout/LearningPageShell";
import { PlanOptions } from "@/components/commerce/PlanOptions";
import { catalogCourses, findCatalogCourse } from "@/data/catalog";

export default async function PlansPage({ searchParams }: PageProps<"/planos">) {
  const requested = (await searchParams).curso;
  const courseId = typeof requested === "string" ? requested : "";
  const course = findCatalogCourse(courseId) ?? catalogCourses.find((item) => item.access === "paid") ?? catalogCourses[0];
  return <LearningPageShell><PlanOptions course={course} /></LearningPageShell>;
}
