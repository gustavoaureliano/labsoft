import type { Metadata } from "next";
import { TeacherMonetization } from "@/components/teacher/TeacherMonetization";

export const metadata: Metadata = {
  title: "Monetização do professor | AprovaAí",
  description: "Relatórios financeiros e de engajamento do professor",
};

export default function TeacherMonetizationPage() {
  return <TeacherMonetization />;
}
