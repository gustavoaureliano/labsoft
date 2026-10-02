export const questionsDemoKey = "aprovaai-demo-student-questions";

export type DemoQuestion = {
  id: number;
  student: string;
  course: string;
  lesson: string;
  prompt: string;
  answer?: string;
};
