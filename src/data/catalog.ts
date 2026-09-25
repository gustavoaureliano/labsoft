export type CatalogCourse = {
  id: string;
  subject: string;
  group: string;
  title: string;
  teacher: string;
  lessonCount: number;
  duration: string;
  rating: number;
  exams: string[];
  summary: string;
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

export const catalogCourses: CatalogCourse[] = [
  {
    id: "fisica-quantica",
    subject: "Física",
    group: "Ciências da Natureza",
    title: "Introdução à Física Quântica",
    teacher: "Prof. Fulano da Silva",
    lessonCount: 42,
    duration: "50h 24min",
    rating: 4.9,
    exams: ["ENEM", "FUVEST"],
    summary: "Conceitos fundamentais da física moderna, da dualidade onda-partícula aos modelos atômicos.",
  },
  {
    id: "biologia-celular",
    subject: "Biologia",
    group: "Ciências da Natureza",
    title: "Biologia Celular para Vestibulares",
    teacher: "Dra. Clara Mendonça",
    lessonCount: 35,
    duration: "33h",
    rating: 4.9,
    exams: ["ENEM", "UNICAMP"],
    summary: "Explore organelas, metabolismo e divisão celular com foco nas questões mais cobradas.",
  },
  {
    id: "estatistica-essencial",
    subject: "Matemática",
    group: "Matemática",
    title: "Estatística Essencial",
    teacher: "Prof. Rafael Costa",
    lessonCount: 28,
    duration: "24h",
    rating: 4.8,
    exams: ["ENEM", "FUVEST"],
    summary: "Interprete gráficos, tabelas e medidas estatísticas com segurança para a prova.",
  },
  {
    id: "redacao-nota-mil",
    subject: "Redação",
    group: "Linguagens",
    title: "Redação nota mil: da tese à conclusão",
    teacher: "Profa. Marina Lopes",
    lessonCount: 20,
    duration: "18h 40min",
    rating: 4.9,
    exams: ["ENEM"],
    summary: "Construa argumentos consistentes e pratique cada etapa do texto dissertativo.",
  },
  {
    id: "quimica-organica",
    subject: "Química",
    group: "Ciências da Natureza",
    title: "Química Orgânica sem mistério",
    teacher: "Prof. Lucas Ribeiro",
    lessonCount: 31,
    duration: "29h 10min",
    rating: 4.7,
    exams: ["ENEM", "FUVEST"],
    summary: "Aprenda funções orgânicas, reações e aplicações presentes no cotidiano.",
  },
  {
    id: "historia-brasil",
    subject: "História",
    group: "Ciências Humanas",
    title: "História do Brasil em perspectiva",
    teacher: "Prof. André Nascimento",
    lessonCount: 26,
    duration: "22h 30min",
    rating: 4.8,
    exams: ["ENEM", "UNICAMP"],
    summary: "Relacione os principais períodos da história brasileira a seus contextos sociais.",
  },
];

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