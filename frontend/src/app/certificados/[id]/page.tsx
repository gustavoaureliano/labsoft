import { AppShell } from "@/components/layout/AppShell";
import { CertificateDetail } from "@/components/learning/Certificates";

export default async function CertificatePage({params}: {params: Promise<{id: string}>}) {
  const {id} = await params;
  return <AppShell activePage="certificates"><CertificateDetail id={id} /></AppShell>;
}
