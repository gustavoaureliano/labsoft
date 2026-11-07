import { NextResponse, type NextRequest } from "next/server";
import { demoRoleCookieName, parseDemoRole, roleHome } from "@/data/demoAccount";
import { requiredRole } from "@/lib/pageAccess";

const publicPaths = new Set(["/", "/login", "/cadastro", "/cadastro/professor", "/recuperar-acesso", "/professor/solicitacao"]);

export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  // Real-mode UI is validated by ApiSessionSync; APIs enforce authorization.
  // A readable role cookie is only a navigation hint, never session proof.
  if (process.env.NEXT_PUBLIC_AUTH_ENABLED === "true") return NextResponse.next();
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
  // API authorization belongs to FastAPI, not page-role redirects.
  matcher: ["/((?!api/|_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
