import { demoCourses, demoTeacherId } from "./demoCourses";

export type DemoFileMetadata = { name: string; type: string; size: number };
export type TeacherLesson = { id: string; title: string; duration: string; videoName: string; videoType?: string; videoSize?: number; thumbnail?: string; thumbnailName?: string; thumbnailType?: string; thumbnailSize?: number };
export type TeacherMaterial = { id: string; title: string; kind: string; fileName?: string; fileType?: string; fileSize?: number };

export type TeacherCourse = {
  id: string;
  title: string;
  subject: string;
  summary: string;
  exams: string;
  access: "free" | "paid";
  price: string;
  status: "Rascunho" | "Publicado";
  students: string;
  image: string;
  lessons: TeacherLesson[];
  materials: TeacherMaterial[];
};

export const teacherCoursesKey = "aprovaai-teacher-courses-demo-v2";

export const initialTeacherCourses: TeacherCourse[] = demoCourses
  .filter((course) => course.ownerId === demoTeacherId)
  .map((course) => ({
    id: course.id,
    title: course.title,
    subject: course.subject,
    summary: course.summary,
    exams: course.exams.join(", "),
    access: course.access,
    price: course.price.toFixed(2).replace(".", ","),
    status: course.status,
    students: course.studentCount ? `${course.studentCount.toLocaleString("pt-BR")} alunos` : "Nenhum aluno",
    image: course.image,
    lessons: course.lessons.map((lesson) => ({
      id: lesson.id,
      title: lesson.title,
      duration: lesson.duration,
      videoName: lesson.videoName ?? `${lesson.id}.mp4`,
      thumbnail: lesson.thumbnail,
    })),
    materials: course.materials,
  }));

export function blankTeacherCourse(): TeacherCourse {
  return {
    id: "",
    title: "",
    subject: "",
    summary: "",
    exams: "",
    access: "free",
    price: "0,00",
    status: "Rascunho",
    students: "Nenhum aluno",
    image: "/images/courses/fisica-quantica.webp",
    lessons: [],
    materials: [],
  };
}
