import { CourseEditor } from "@/components/teacher/CourseEditor";
import { CourseEditorIntegrated } from "@/components/teacher/CourseEditorIntegrated";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default async function EditCoursePage({ params }: PageProps<"/professor/cursos/[id]/editar">) {
  const {id} = await params;
  return <TeacherShell activePage="courses">{process.env.NEXT_PUBLIC_AUTH_ENABLED === "true" ? <CourseEditorIntegrated courseId={id} /> : <CourseEditor courseId={id} />}</TeacherShell>;
}
