export const lessonInteractionsKey = "aprovaai-demo-lesson-interactions";
export const lessonReportKey = "aprovaai-demo-lesson-report";

export type LessonInteractions = { comments: string[]; note: string; rating: number };
export type LessonReport = { reason: string; decision?: "mantido" | "ocultado" };
export const initialLessonInteractions: LessonInteractions = { comments: [], note: "", rating: 0 };
