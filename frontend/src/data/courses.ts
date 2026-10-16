export type EnrolledLesson = {
  id: string;
  number: string;
  title: string;
  duration: string;
  status: "Concluída" | "Aula atual" | "Próxima aula";
  description: string;
  thumbnail?: string;
};

const course = findDemoCourse("fisica-enem-mecanica")!;
const currentLessonId = "leis-newton";
const currentLessonIndex = course.lessons.findIndex((lesson) => lesson.id === currentLessonId);
const lessons: EnrolledLesson[] = course.lessons.map((lesson, index) => ({
  id: lesson.id,
  number: String(index + 1).padStart(2, "0"),
  title: lesson.title,
  duration: lesson.duration,
  status: index < currentLessonIndex ? "Concluída" : index === currentLessonIndex ? "Aula atual" : "Próxima aula",
  description: lesson.description,
  thumbnail: lesson.thumbnail,
}));

export const enrolledCourse = {
  id: course.id,
  image: course.image,
  category: course.subject,
  title: course.title,
  teacher: course.teacher,
  teacherInitials: "FS",
  summary: course.summary,
  totalLessons: lessons.length,
  progress: 68,
  currentLessonId,
  lessons,
  modules: [
    { title: "Cinemática", lessonIds: lessons.slice(0, 6).map((lesson) => lesson.id) },
    { title: "Dinâmica e energia", lessonIds: lessons.slice(6).map((lesson) => lesson.id) },
  ],
};

export const currentLesson = lessons.find((lesson) => lesson.id === enrolledCourse.currentLessonId)!;

export function findEnrolledLesson(id?: string) {
  return enrolledCourse.lessons.find((lesson) => lesson.id === id) ?? currentLesson;
}

export type LessonCollectionContext =
  | { origin: "course" }
  | { origin: "history" | "favorites" }
  | { origin: "playlist"; playlistId: string };

export function lessonsFromIds(ids: string[]) {
  return ids.flatMap((id) => {
    const lesson = enrolledCourse.lessons.find((item) => item.id === id);
    return lesson ? [lesson] : [];
  });
}

export function lessonHref(lessonId: string, context: LessonCollectionContext = { origin: "course" }) {
  const params = new URLSearchParams({ curso: enrolledCourse.id, aula: lessonId });
  if (context.origin !== "course") params.set("origem", context.origin);
  if (context.origin === "playlist") params.set("lista", context.playlistId);
  return `/videoaula?${params.toString()}`;
}

export function questionHref(lessonId?: string) {
  const params = new URLSearchParams({ curso: enrolledCourse.id });
  if (lessonId) params.set("aula", lessonId);
  return `/duvidas?${params.toString()}`;
}
import { findDemoCourse } from "./demoCourses";
