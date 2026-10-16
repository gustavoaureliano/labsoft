export const demoAccountKey = "aprovaai-demo-account";
export const teacherApplicationKey = "aprovaai-demo-teacher-application";
export const demoRoleCookieName = "aprovaai_demo_role";

export type DemoRole = "student" | "teacher" | "admin";

export const roleHome: Record<DemoRole, string> = {
  student: "/",
  teacher: "/professor/cursos",
  admin: "/admin",
};

export function parseDemoRole(value?: string): DemoRole | null {
  return value === "student" || value === "teacher" || value === "admin" ? value : null;
}

export type DemoAccount = { name: string; email: string; role: DemoRole };
export type TeacherApplication = { name: string; email: string; area: string; status: "pending" | "approved" | "rejected" };
