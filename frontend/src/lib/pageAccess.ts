import type { DemoRole } from "@/data/demoAccount";

const studentPaths = new Set(["/meus-cursos", "/videoaula", "/duvidas", "/perfil", "/avisos", "/explorar-cursos", "/materiais-complementares", "/pesquisa", "/checkout", "/assinatura"]);

export function requiredRole(pathname: string): DemoRole | null {
  if (pathname === "/certificados/verificar" || pathname.startsWith("/certificados/verificar/")) return null;
  if (studentPaths.has(pathname) || pathname.startsWith("/meus-cursos/") || pathname === "/certificados" || pathname.startsWith("/certificados/")) return "student";
  if (pathname === "/professor/cursos" || pathname.startsWith("/professor/cursos/") || pathname === "/professor/duvidas" || pathname === "/professor/monetizacao") return "teacher";
  if (pathname === "/admin" || pathname.startsWith("/admin/")) return "admin";
  return null;
}
