import type { Metadata } from "next";
import { ModerationDashboard } from "@/components/admin/ModerationDashboard";

export const metadata: Metadata = {
  title: "Moderação e qualidade | Logos Academy",
  description: "Filas de moderação e análise de qualidade da Logos Academy",
};

export default function ModerationPage() {
  return <ModerationDashboard />;
}
