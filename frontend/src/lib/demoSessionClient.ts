import { demoRoleCookieName, type DemoRole } from "@/data/demoAccount";

const roleToDemoUser: Record<DemoRole, string> = {
  student: "aluno-demo",
  teacher: "professor-demo",
  admin: "admin-demo",
};

export function setDemoRole(role: DemoRole) {
  document.cookie = `${demoRoleCookieName}=${role}; Path=/; SameSite=Lax; Max-Age=2592000`;
  document.cookie = `aprovaai_demo_user=${roleToDemoUser[role]}; Path=/; SameSite=Lax; Max-Age=2592000`;
}

export function clearDemoRole() {
  document.cookie = `${demoRoleCookieName}=; Path=/; SameSite=Lax; Max-Age=0`;
  document.cookie = "aprovaai_demo_user=; Path=/; SameSite=Lax; Max-Age=0";
}
