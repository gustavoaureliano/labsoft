export function courseLessonsHref(courseId: string) {
  return `/professor/cursos/${encodeURIComponent(courseId)}/aulas`;
}

export function editLessonHref(courseId: string, lessonId: string) {
  return `${courseLessonsHref(courseId)}/${encodeURIComponent(lessonId)}/editar`;
}

export function durationLabel(seconds?: number | null) {
  if (seconds == null) return "Duração não informada";
  return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
}
