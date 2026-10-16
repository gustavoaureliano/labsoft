import { demoRoleCookieName, type DemoRole } from "@/data/demoAccount";

export function setDemoRole(role: DemoRole) {
  document.cookie = `${demoRoleCookieName}=${role}; Path=/; SameSite=Lax; Max-Age=2592000`;
}

export function clearDemoRole() {
  document.cookie = `${demoRoleCookieName}=; Path=/; SameSite=Lax; Max-Age=0`;
}
