import { notFound } from "next/navigation";
import { CourseDetails } from "@/components/commerce/CourseDetails";
import { LearningPageShell } from "@/components/layout/LearningPageShell";
import { catalogCourses, findCatalogCourse } from "@/data/catalog";

export function generateStaticParams() {
  return catalogCourses.map((course) => ({ id: course.id }));
}

export default async function CourseDetailsPage({ params }: PageProps<"/cursos/[id]">) {
  const course = findCatalogCourse((await params).id);
  if (!course) notFound();
  return <LearningPageShell><CourseDetails course={course} /></LearningPageShell>;
}
