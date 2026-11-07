import type { CatalogCourse, ComplementaryMaterial } from "@/data/catalog";
import type { ApiCourseSummary, ApiLesson, ApiMaterial } from "./types";

const fallbackCover = "/images/courses/fisica-quantica.webp";

export function toCatalogCourse(
  course: ApiCourseSummary,
  lessons: ApiLesson[] = [],
): CatalogCourse {
  const durationMinutes = lessons.reduce((total, lesson) => total + lesson.duration_minutes, 0);
  const sections = new Map<string, string[]>();
  for (const lesson of lessons) {
    const title = lesson.section_title || "Aulas do curso";
    sections.set(title, [...(sections.get(title) ?? []), lesson.title]);
  }
  return {
    id: course.id,
    image: course.cover_url ?? fallbackCover,
    subject: course.subject,
    group: course.area,
    title: course.title,
    teacher: course.teacher_name,
    lessonCount: course.lesson_count,
    duration: durationMinutes ? `${durationMinutes} min` : "Ritmo flexível",
    rating: course.rating ?? 0,
    exams: course.exams,
    summary: course.summary,
    audience: course.audience ?? "Estudantes de vestibular",
    access: course.access_type,
    price: Number(course.price ?? 0),
    syllabus: [...sections].map(([title, titles]) => ({ title, lessons: titles })),
  };
}

export function toComplementaryMaterial(
  material: ApiMaterial,
  courseTitle = "Curso relacionado",
): ComplementaryMaterial {
  return {
    id: material.id,
    courseId: material.course_id,
    courseTitle,
    type: material.kind,
    title: material.title,
    description: material.description,
    format: material.external_url ? "Link" : material.kind.toUpperCase(),
  };
}
