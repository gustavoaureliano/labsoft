export type LessonNavigationOrigin = "course-editor";

export function courseLessonsHref(courseId: string, origin?: LessonNavigationOrigin) {
  const path = `/professor/cursos/${encodeURIComponent(courseId)}/aulas`;
  return origin ? `${path}?origem=${origin}` : path;
}

export function editLessonHref(courseId: string, lessonId: string, origin?: LessonNavigationOrigin, preview = false) {
  const path = `${courseLessonsHref(courseId)}/${encodeURIComponent(lessonId)}/editar`;
  const query = new URLSearchParams();
  if (origin) query.set("origem", origin);
  if (preview) query.set("modo", "previa");
  return query.size ? `${path}?${query}` : path;
}

export function durationLabel(seconds?: number | null) {
  if (seconds == null) return "Duração não informada";
  return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
}
