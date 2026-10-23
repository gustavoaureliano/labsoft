import { CourseEditorIntegrated } from "@/components/teacher/CourseEditorIntegrated";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default function NewCoursePage() {
  return <TeacherShell activePage="courses"><CourseEditorIntegrated /></TeacherShell>;
}
