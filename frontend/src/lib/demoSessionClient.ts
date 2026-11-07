import { demoRoleCookieName, type DemoRole } from "@/data/demoAccount";

export function setDemoRole(role: DemoRole) {
  document.cookie = `${demoRoleCookieName}=${role}; Path=/; SameSite=Lax; Max-Age=2592000`;
  const user = role === "student" ? "aluno-demo" : role === "teacher" ? "professor-demo" : "";
  document.cookie = `aprovaai_demo_user=${user}; Path=/; SameSite=Lax; Max-Age=2592000`;
}

export function clearDemoRole() {
  document.cookie = `${demoRoleCookieName}=; Path=/; SameSite=Lax; Max-Age=0`;
  document.cookie = "aprovaai_demo_user=; Path=/; SameSite=Lax; Max-Age=0";
}
