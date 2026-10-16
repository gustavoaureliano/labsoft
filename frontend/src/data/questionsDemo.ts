export const questionsDemoKey = "aprovaai-demo-student-questions";

export type DemoQuestion = {
  id: number;
  student: string;
  courseId: string;
  course: string;
  lessonId?: string;
  lesson: string;
  prompt: string;
  answer?: string;
};
