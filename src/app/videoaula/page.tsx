import { AppShell } from "@/components/layout/AppShell";
import { VideoLessonExperience } from "./VideoLessonExperience";

export default async function VideoAula({ searchParams }: PageProps<"/videoaula">) {
  const query = await searchParams;

  return (
    <AppShell activePage="courses">
      <VideoLessonExperience
        lessonId={typeof query.aula === "string" ? query.aula : undefined}
        origin={typeof query.origem === "string" ? query.origem : undefined}
        playlistId={typeof query.lista === "string" ? query.lista : undefined}
      />
    </AppShell>
  );
}
