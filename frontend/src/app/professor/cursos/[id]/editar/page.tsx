import { CourseEditorIntegrated } from "@/components/teacher/CourseEditorIntegrated";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default async function EditCoursePage({ params }: PageProps<"/professor/cursos/[id]/editar">) {
  return <TeacherShell activePage="courses"><CourseEditorIntegrated courseId={(await params).id} /></TeacherShell>;
}
