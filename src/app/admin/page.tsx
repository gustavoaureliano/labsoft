import type { Metadata } from "next";
import { AdminDashboard } from "@/components/admin/AdminDashboard";

export const metadata: Metadata = {
  title: "Visão geral do negócio | AprovaAí",
  description: "Painel administrativo de desempenho da AprovaAí",
};

export default function AdminPage() {
  return <AdminDashboard />;
}
