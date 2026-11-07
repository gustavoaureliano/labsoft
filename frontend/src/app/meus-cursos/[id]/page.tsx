import { AppShell } from "@/components/layout/AppShell";
import { LearningCoursePage } from "@/components/learning/LearningCoursePage";

export default async function StudentCoursePage({ params }: PageProps<"/meus-cursos/[id]">) {
  const {id} = await params;

  return (
    <AppShell activePage="courses">
      <LearningCoursePage id={id} />
    </AppShell>
  );
}
