import { notFound } from "next/navigation";
import type { CatalogCourse } from "@/data/catalog";
import { toCatalogCourse } from "@/lib/api/adapters";
import { apiRequest } from "@/lib/api/client";
import type { ApiCourseDetails, ApiCoursePage } from "@/lib/api/types";

export async function courseForCheckout(requestedId: string): Promise<CatalogCourse> {
  let courseId = requestedId;
  if (!courseId) {
    const page = await apiRequest<ApiCoursePage>("/api/courses?page=1&size=1");
    if (!page.items.length) notFound();
    courseId = page.items[0].id;
  }
  const details = await apiRequest<ApiCourseDetails>(`/api/courses/${encodeURIComponent(courseId)}`);
  return toCatalogCourse(details.course, details.lessons);
}
