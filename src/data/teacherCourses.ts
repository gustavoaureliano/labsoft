export type DemoFileMetadata = { name: string; type: string; size: number };
export type TeacherLesson = { id: string; title: string; duration: string; videoName: string; videoType?: string; videoSize?: number };
export type TeacherMaterial = { id: string; title: string; kind: string; fileName?: string; fileType?: string; fileSize?: number };

export type TeacherCourse = {
  id: string;
  title: string;
  subject: string;
  summary: string;
  exams: string;
  access: "free" | "paid";
  price: string;
  status: "Rascunho" | "Publicado";
  students: string;
  image: string;
  lessons: TeacherLesson[];
  materials: TeacherMaterial[];
};

export const teacherCoursesKey = "aprovaai-teacher-courses-demo";

export const initialTeacherCourses: TeacherCourse[] = [
  {
    id: "fisica-quantica",
    title: "Introdução à Física Quântica",
    subject: "Física",
    summary: "Conceitos fundamentais da física moderna para vestibulares.",
    exams: "ENEM, FUVEST",
    access: "paid",
    price: "29,90",
    status: "Publicado",
    students: "12.420 alunos",
    image: "/images/courses/fisica-quantica.webp",
    lessons: [
      { id: "q1", title: "Introdução e contexto histórico", duration: "18 min", videoName: "introducao.mp4" },
      { id: "q2", title: "Radiação de corpo negro", duration: "24 min", videoName: "radiacao.mp4" },
      { id: "q3", title: "Efeito fotoelétrico", duration: "21 min", videoName: "efeito-fotoeletrico.mp4" },
    ],
    materials: [{ id: "qm1", title: "Resumo de física moderna", kind: "PDF" }],
  },
  {
    id: "termodinamica",
    title: "Termodinâmica Avançada",
    subject: "Física",
    summary: "Curso em preparação sobre processos e ciclos termodinâmicos.",
    exams: "FUVEST",
    access: "paid",
    price: "24,90",
    status: "Rascunho",
    students: "Nenhum aluno",
    image: "/teacher-thermo.png",
    lessons: [],
    materials: [],
  },
  {
    id: "cinematica",
    title: "Cinemática e Dinâmica para ENEM",
    subject: "Física",
    summary: "Movimento, forças e aplicações para questões do ENEM.",
    exams: "ENEM",
    access: "free",
    price: "0,00",
    status: "Publicado",
    students: "6.000 alunos",
    image: "/images/courses/fisica-mecanica.webp",
    lessons: [
      { id: "c1", title: "Movimento uniforme", duration: "20 min", videoName: "movimento.mp4" },
      { id: "c2", title: "Leis de Newton", duration: "25 min", videoName: "newton.mp4" },
    ],
    materials: [],
  },
];

export function blankTeacherCourse(): TeacherCourse {
  return {
    id: "",
    title: "",
    subject: "",
    summary: "",
    exams: "",
    access: "free",
    price: "0,00",
    status: "Rascunho",
    students: "Nenhum aluno",
    image: "/images/courses/fisica-quantica.webp",
    lessons: [],
    materials: [],
  };
}
