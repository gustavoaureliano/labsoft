import { demoCourses } from "./demoCourses";

export type CatalogCourse = {
  id: string;
  image: string;
  subject: string;
  group: string;
  title: string;
  teacher: string;
  lessonCount: number;
  duration: string;
  rating: number;
  exams: string[];
  summary: string;
  audience: string;
  access: "free" | "paid";
  price: number;
  syllabus: { title: string; lessons: string[] }[];
};

export type ComplementaryMaterial = {
  id: string;
  courseId: string;
  courseTitle: string;
  type: string;
  title: string;
  description: string;
  format: string;
};

export const courseGroups = ["Matemática", "Linguagens", "Ciências da Natureza", "Ciências Humanas"];

export const catalogCourses: CatalogCourse[] = demoCourses
  .filter((course) => course.status === "Publicado")
  .map(({ id, image, subject, group, title, teacher, lessonCount, duration, rating, exams, summary, audience, access, price, syllabus }) => ({
    id,
    image,
    subject,
    group,
    title,
    teacher,
    lessonCount,
    duration,
    rating,
    exams,
    summary,
    audience,
    access,
    price,
    syllabus,
  }));

export function findCatalogCourse(id: string) {
  return catalogCourses.find((course) => course.id === id);
}

export function formatPrice(value: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

export const complementaryMaterials: ComplementaryMaterial[] = [
  {
    id: "mapa-quantica",
    courseId: "fisica-quantica",
    courseTitle: "Introdução à Física Quântica",
    type: "Mapa mental",
    title: "Dualidade onda-partícula",
    description: "Um resumo visual dos conceitos centrais e experimentos históricos.",
    format: "PDF · 2 páginas",
  },
  {
    id: "exercicios-quantica",
    courseId: "fisica-quantica",
    courseTitle: "Introdução à Física Quântica",
    type: "Exercícios",
    title: "Lista de exercícios: modelos atômicos",
    description: "12 questões comentadas para revisar a estrutura da matéria.",
    format: "PDF · 12 questões",
  },
  {
    id: "resumo-celula",
    courseId: "biologia-celular",
    courseTitle: "Biologia Celular para Vestibulares",
    type: "Resumo",
    title: "Organelas e suas funções",
    description: "Quadro comparativo para memorizar as estruturas celulares.",
    format: "PDF · 4 páginas",
  },
  {
    id: "simulado-celula",
    courseId: "biologia-celular",
    courseTitle: "Biologia Celular para Vestibulares",
    type: "Simulado",
    title: "Revisão de citologia",
    description: "Questões de vestibulares recentes com gabarito explicado.",
    format: "Online · 10 questões",
  },
  {
    id: "formula-estatistica",
    courseId: "estatistica-essencial",
    courseTitle: "Estatística Essencial",
    type: "Resumo",
    title: "Fórmulas de estatística",
    description: "Média, mediana, moda e dispersão em uma folha de consulta.",
    format: "PDF · 1 página",
  },
  {
    id: "proposta-redacao",
    courseId: "redacao-nota-mil",
    courseTitle: "Redação nota mil: da tese à conclusão",
    type: "Exercícios",
    title: "Propostas de redação para praticar",
    description: "Temas atuais com repertórios para iniciar seu planejamento.",
    format: "PDF · 6 propostas",
  },
];

export const materialTypes = [...new Set(complementaryMaterials.map((material) => material.type))];

function normalizeSearchText(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
}

export function searchCatalogCourses(query: string) {
  const normalizedQuery = normalizeSearchText(query.trim());
  if (!normalizedQuery) return [];

  return catalogCourses.filter((course) =>
    normalizeSearchText([
      course.title,
      course.subject,
      course.group,
      course.teacher,
      course.summary,
      ...course.exams,
    ].join(" ")).includes(normalizedQuery),
  );
}

export function searchCatalogMaterials(query: string) {
  const normalizedQuery = normalizeSearchText(query.trim());
  if (!normalizedQuery) return [];

  return complementaryMaterials.filter((material) =>
    normalizeSearchText([
      material.title,
      material.description,
      material.courseTitle,
      material.type,
    ].join(" ")).includes(normalizedQuery),
  );
}
