import type { DemoRole } from "@/data/demoAccount";

const studentPaths = new Set(["/meus-cursos", "/videoaula", "/duvidas", "/perfil", "/explorar-cursos", "/materiais-complementares", "/pesquisa", "/checkout", "/assinatura"]);

// Stable references: callers use the result as an effect dependency.
const studentOnly: readonly DemoRole[] = ["student"];
const teacherOnly: readonly DemoRole[] = ["teacher"];
const adminOnly: readonly DemoRole[] = ["admin"];
// The engagement service notifies both students and teachers.
const notificationRoles: readonly DemoRole[] = ["student", "teacher"];

export function requiredRoles(pathname: string): readonly DemoRole[] | null {
  if (pathname === "/certificados/verificar" || pathname.startsWith("/certificados/verificar/")) return null;
  if (pathname === "/avisos") return notificationRoles;
  if (studentPaths.has(pathname) || pathname.startsWith("/meus-cursos/") || pathname === "/certificados" || pathname.startsWith("/certificados/")) return studentOnly;
  if (pathname === "/professor/cursos" || pathname.startsWith("/professor/cursos/") || pathname === "/professor/duvidas" || pathname === "/professor/monetizacao") return teacherOnly;
  if (pathname === "/admin" || pathname.startsWith("/admin/")) return adminOnly;
  return null;
}
