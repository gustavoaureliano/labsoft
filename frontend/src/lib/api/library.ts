import type { Course, Lesson } from "./learning";

// Browser-local library remains the other domain's demo adapter.
// Unknown/old IDs are retained in storage and never remapped to different lessons.
export function resolveLessons(ids: string[], courses: Course[]): Lesson[] {
  const lessons = new Map(courses.flatMap(course => course.lessons).map(lesson => [lesson.id, lesson]));
  return ids.flatMap(id => {const lesson = lessons.get(id); return lesson ? [lesson] : [];});
}
