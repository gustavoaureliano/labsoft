import { ProfilePage } from "@/components/profile/page";
import { AppShell } from "@/components/layout/AppShell";

export default function Perfil() {
  return (
    <AppShell activePage="profile" showSearch={false}>
      <ProfilePage />
    </AppShell>
  );
}