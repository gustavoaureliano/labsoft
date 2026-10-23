import { LessonEditor } from "@/components/teacher/LessonEditor";
import { TeacherShell } from "@/components/teacher/TeacherShell";

export default async function EditLessonPage({ params, searchParams }: {
  params: Promise<{ id: string; lessonId: string }>;
  searchParams: Promise<{ modo?: string }>;
}) {
  const { id, lessonId } = await params;
  const { modo } = await searchParams;
  return <TeacherShell activePage="courses"><LessonEditor key={`${id}:${lessonId}`} courseId={id} lessonId={lessonId} initialPreview={modo === "previa"} /></TeacherShell>;
}
