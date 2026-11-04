import { CourseLessons } from "@/components/teacher/CourseLessons";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default async function CourseLessonsPage({ params, searchParams }: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ origem?: string }>;
}) {
  const { id } = await params;
  const { origem } = await searchParams;
  return <TeacherShell activePage="courses"><CourseLessons courseId={id} origin={origem === "course-editor" ? origem : undefined} /></TeacherShell>;
}
