import type { Metadata } from "next";
import { AdminDashboard } from "@/components/admin/AdminDashboard";

export const metadata: Metadata = {
  title: "Visão geral do negócio | Logos Academy",
  description: "Painel administrativo de desempenho da Logos Academy",
};

export default function AdminPage() {
  return <AdminDashboard />;
}
