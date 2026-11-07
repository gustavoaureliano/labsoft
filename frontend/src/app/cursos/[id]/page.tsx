import { notFound } from "next/navigation";
import { CourseDetails } from "@/components/commerce/CourseDetails";
import { LearningPageShell } from "@/components/layout/LearningPageShell";
import { toCatalogCourse } from "@/lib/api/adapters";
import { ApiError, apiRequest, studentHeaders } from "@/lib/api/client";
import type { ApiCourseDetails } from "@/lib/api/types";

export default async function CourseDetailsPage({ params }: PageProps<"/cursos/[id]">) {
  const id = (await params).id;
  let details: ApiCourseDetails;
  try {
    details = await apiRequest<ApiCourseDetails>(`/api/courses/${id}`, { headers: studentHeaders() });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
  const course = toCatalogCourse(details.course, details.lessons);
  return <LearningPageShell><CourseDetails course={course} /></LearningPageShell>;
}
