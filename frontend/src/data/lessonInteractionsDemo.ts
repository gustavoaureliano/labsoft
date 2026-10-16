export const lessonInteractionsKey = "aprovaai-demo-lesson-interactions";
export const lessonReportKey = "aprovaai-demo-lesson-report";

export function lessonInteractionsStorageKey(lessonId: string) {
  return lessonId === "leis-newton" ? lessonInteractionsKey : `${lessonInteractionsKey}:${lessonId}`;
}

export function lessonReportStorageKey(lessonId: string) {
  return lessonId === "leis-newton" ? lessonReportKey : `${lessonReportKey}:${lessonId}`;
}

export type LessonInteractions = { comments: string[]; note: string; rating: number };
export type LessonReport = { reason: string; lessonId?: string; lessonTitle?: string; decision?: "mantido" | "ocultado" };
export const initialLessonInteractions: LessonInteractions = { comments: [], note: "", rating: 0 };
