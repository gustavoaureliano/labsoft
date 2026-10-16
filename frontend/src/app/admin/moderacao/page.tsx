import type { Metadata } from "next";
import { ModerationDashboard } from "@/components/admin/ModerationDashboard";

export const metadata: Metadata = {
  title: "Moderação e qualidade | AprovaAí",
  description: "Filas de moderação e análise de qualidade da AprovaAí",
};

export default function ModerationPage() {
  return <ModerationDashboard />;
}
