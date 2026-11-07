import { CourseEditor } from "@/components/teacher/CourseEditor";
import { CourseEditorIntegrated } from "@/components/teacher/CourseEditorIntegrated";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default function NewCoursePage() {
  return <TeacherShell activePage="courses">{process.env.NEXT_PUBLIC_AUTH_ENABLED === "true" ? <CourseEditorIntegrated /> : <CourseEditor />}</TeacherShell>;
}
