import { NextResponse, type NextRequest } from "next/server";
import { demoRoleCookieName, parseDemoRole, roleHome, type DemoRole } from "@/data/demoAccount";

const publicPaths = new Set(["/login", "/cadastro", "/cadastro/professor", "/recuperar-acesso", "/professor/solicitacao"]);
const studentPaths = new Set(["/", "/meus-cursos", "/videoaula", "/duvidas", "/perfil", "/avisos", "/explorar-cursos", "/materiais-complementares", "/pesquisa"]);

function requiredRole(pathname: string): DemoRole | null {
  if (studentPaths.has(pathname) || pathname === "/certificados" || pathname.startsWith("/certificados/")) return "student";
  if (pathname === "/professor/cursos" || pathname === "/professor/duvidas" || pathname === "/professor/monetizacao") return "teacher";
  if (pathname === "/admin" || pathname.startsWith("/admin/")) return "admin";
  return null;
}

export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (publicPaths.has(pathname)) return NextResponse.next();

  const role = parseDemoRole(request.cookies.get(demoRoleCookieName)?.value);
  const destination = (path: string) => NextResponse.redirect(new URL(path, request.url));

  if (pathname === "/duvidas/aluno") return destination(role === "student" ? "/duvidas" : role ? roleHome[role] : "/login");

  const expectedRole = requiredRole(pathname);
  if (!expectedRole) return NextResponse.next();
  if (!role) return destination("/login");
  if (role !== expectedRole) return destination(roleHome[role]);
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
