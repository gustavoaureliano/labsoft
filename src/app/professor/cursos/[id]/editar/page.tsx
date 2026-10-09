import { CourseEditor } from "@/components/teacher/CourseEditor";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default async function EditCoursePage({ params }: PageProps<"/professor/cursos/[id]/editar">) {
  return <TeacherShell activePage="courses"><CourseEditor courseId={(await params).id} /></TeacherShell>;
}
