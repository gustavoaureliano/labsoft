import { ProfilePage } from "@/components/profile/page";
import { AppShell } from "@/components/layout/AppShell";

export default function Perfil() {
  return (
    <AppShell activeItem="Meu perfil" showSearch={false}>
      <ProfilePage />
    </AppShell>
  );
}