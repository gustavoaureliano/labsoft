import { AppShell } from "@/components/layout/AppShell";
import { PlaylistDetails } from "@/components/learning/PlaylistDetails";

export default async function PlaylistPage({ params }: PageProps<"/meus-cursos/playlists/[id]">) {
  const { id } = await params;

  return (
    <AppShell activePage="courses">
      <PlaylistDetails playlistId={id} />
    </AppShell>
  );
}
