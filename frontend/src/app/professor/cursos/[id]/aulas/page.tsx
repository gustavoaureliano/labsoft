import { CourseLessons } from "@/components/teacher/CourseLessons";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default async function CourseLessonsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TeacherShell activePage="courses"><CourseLessons courseId={id} /></TeacherShell>;
}
