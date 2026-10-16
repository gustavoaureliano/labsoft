import { CourseEditor } from "@/components/teacher/CourseEditor";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default function NewCoursePage() {
  return <TeacherShell activePage="courses"><CourseEditor /></TeacherShell>;
}
