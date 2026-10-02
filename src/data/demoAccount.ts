export const demoAccountKey = "aprovaai-demo-account";
export const teacherApplicationKey = "aprovaai-demo-teacher-application";

export type DemoAccount = { name: string; email: string; role: "student" | "teacher" | "admin" };
export type TeacherApplication = { name: string; email: string; area: string; status: "pending" | "approved" | "rejected" };
