export type DemoCourseLesson = {
  id: string;
  title: string;
  duration: string;
  description: string;
  videoName?: string;
  thumbnail?: string;
};

export type DemoCourseMaterial = {
  id: string;
  title: string;
  kind: string;
};

export type DemoCourse = {
  id: string;
  ownerId?: string;
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
  status: "Rascunho" | "Publicado";
  studentCount: number;
  syllabus: { title: string; lessons: string[] }[];
  lessons: DemoCourseLesson[];
  materials: DemoCourseMaterial[];
};

export const demoTeacherId = "professor-demo";

const mechanicsLessons: DemoCourseLesson[] = [
  { id: "grandezas-vetores", title: "Grandezas e vetores", duration: "18 min", description: "Revise grandezas escalares, vetoriais e suas representações." },
  { id: "movimento-uniforme", title: "Movimento uniforme", duration: "22 min", description: "Entenda velocidade constante e interprete gráficos de movimento." },
  { id: "movimento-variado", title: "Movimento uniformemente variado", duration: "26 min", description: "Relacione aceleração, velocidade e posição em movimentos variados." },
  { id: "queda-livre", title: "Queda livre", duration: "19 min", description: "Aplique as equações do movimento à queda dos corpos." },
  { id: "lancamentos", title: "Lançamentos vertical e oblíquo", duration: "28 min", description: "Analise lançamentos decompondo o movimento em seus eixos." },
  { id: "movimento-aceleracao", title: "Movimento e aceleração", duration: "21 min", description: "Consolide a relação entre movimento, velocidade e aceleração." },
  { id: "introducao-forcas", title: "Introdução às forças", duration: "20 min", description: "Reconheça as principais forças presentes em problemas de mecânica." },
  { id: "leis-newton", title: "Leis de Newton e suas aplicações", duration: "24 min", description: "Entenda as três leis de Newton e veja como elas ajudam a explicar situações do dia a dia.", thumbnail: "/images/video/leis-de-newton.webp" },
  { id: "exercicios-dinamica", title: "Exercícios de dinâmica", duration: "30 min", description: "Resolva problemas de força resultante e movimento." },
  { id: "trabalho-energia", title: "Trabalho e energia", duration: "25 min", description: "Relacione trabalho mecânico, energia e potência." },
  { id: "impulso-quantidade", title: "Impulso e quantidade de movimento", duration: "23 min", description: "Estude colisões, impulso e conservação da quantidade de movimento." },
  { id: "revisao-mecanica", title: "Revisão de mecânica", duration: "32 min", description: "Revise os conceitos do curso com questões de vestibular." },
];

const quantumLessons: DemoCourseLesson[] = [
  { id: "q1", title: "Introdução e contexto histórico", duration: "18 min", description: "Conheça o contexto que levou ao surgimento da física quântica.", videoName: "introducao.mp4" },
  { id: "q2", title: "Radiação de corpo negro", duration: "24 min", description: "Entenda o problema da radiação de corpo negro e a quantização da energia.", videoName: "radiacao.mp4" },
  { id: "q3", title: "Efeito fotoelétrico", duration: "21 min", description: "Relacione luz, frequência e emissão de elétrons.", videoName: "efeito-fotoeletrico.mp4" },
];

export const demoCourses: DemoCourse[] = [
  {
    id: "fisica-quantica",
    ownerId: demoTeacherId,
    image: "/images/courses/fisica-quantica.webp",
    subject: "Física",
    group: "Ciências da Natureza",
    title: "Introdução à Física Quântica",
    teacher: "Prof. Fulano da Silva",
    lessonCount: quantumLessons.length,
    duration: "1h 03min",
    rating: 4.9,
    exams: ["ENEM", "FUVEST"],
    summary: "Conceitos fundamentais da física moderna para vestibulares.",
    audience: "Estudantes que querem revisar física moderna para o ENEM e vestibulares.",
    access: "paid",
    price: 29.9,
    status: "Publicado",
    studentCount: 12420,
    syllabus: [{ title: "Fundamentos", lessons: quantumLessons.map((lesson) => lesson.title) }],
    lessons: quantumLessons,
    materials: [
      { id: "mapa-quantica", title: "Dualidade onda-partícula", kind: "PDF" },
      { id: "exercicios-quantica", title: "Lista de exercícios: modelos atômicos", kind: "PDF" },
    ],
  },
  {
    id: "fisica-enem-mecanica",
    ownerId: demoTeacherId,
    image: "/images/courses/fisica-mecanica.webp",
    subject: "Física",
    group: "Ciências da Natureza",
    title: "Física para o ENEM: Mecânica",
    teacher: "Prof. Fulano da Silva",
    lessonCount: mechanicsLessons.length,
    duration: "4h 48min",
    rating: 4.8,
    exams: ["ENEM"],
    summary: "Aprenda cinemática, dinâmica e energia com foco nas situações mais frequentes do ENEM.",
    audience: "Estudantes que querem revisar os principais temas de mecânica para o ENEM.",
    access: "free",
    price: 0,
    status: "Publicado",
    studentCount: 6000,
    syllabus: [
      { title: "Cinemática", lessons: mechanicsLessons.slice(0, 6).map((lesson) => lesson.title) },
      { title: "Dinâmica e energia", lessons: mechanicsLessons.slice(6).map((lesson) => lesson.title) },
    ],
    lessons: mechanicsLessons,
    materials: [],
  },
  {
    id: "termodinamica",
    ownerId: demoTeacherId,
    image: "/teacher-thermo.png",
    subject: "Física",
    group: "Ciências da Natureza",
    title: "Termodinâmica Avançada",
    teacher: "Prof. Fulano da Silva",
    lessonCount: 0,
    duration: "Em preparação",
    rating: 0,
    exams: ["FUVEST"],
    summary: "Curso em preparação sobre processos e ciclos termodinâmicos.",
    audience: "Estudantes que querem aprofundar seus conhecimentos de termodinâmica.",
    access: "paid",
    price: 24.9,
    status: "Rascunho",
    studentCount: 0,
    syllabus: [],
    lessons: [],
    materials: [],
  },
  {
    id: "biologia-celular",
    image: "/images/courses/biologia-celular.webp",
    subject: "Biologia",
    group: "Ciências da Natureza",
    title: "Biologia Celular para Vestibulares",
    teacher: "Dra. Clara Mendonça",
    lessonCount: 35,
    duration: "33h",
    rating: 4.9,
    exams: ["ENEM", "UNICAMP"],
    summary: "Explore organelas, metabolismo e divisão celular com foco nas questões mais cobradas.",
    audience: "Estudantes que desejam dominar citologia e os temas mais recorrentes nas provas.",
    access: "paid",
    price: 24.9,
    status: "Publicado",
    studentCount: 8300,
    syllabus: [
      { title: "Estrutura celular", lessons: ["Tipos de célula", "Organelas", "Membrana plasmática"] },
      { title: "Processos celulares", lessons: ["Metabolismo", "Mitose e meiose", "Questões comentadas"] },
    ],
    lessons: [],
    materials: [],
  },
  {
    id: "estatistica-essencial",
    image: "/images/courses/estatistica.webp",
    subject: "Matemática",
    group: "Matemática",
    title: "Estatística Essencial",
    teacher: "Prof. Rafael Costa",
    lessonCount: 28,
    duration: "24h",
    rating: 4.8,
    exams: ["ENEM", "FUVEST"],
    summary: "Interprete gráficos, tabelas e medidas estatísticas com segurança para a prova.",
    audience: "Estudantes que precisam interpretar dados e resolver questões de estatística básica.",
    access: "free",
    price: 0,
    status: "Publicado",
    studentCount: 10400,
    syllabus: [
      { title: "Leitura de dados", lessons: ["Tabelas e gráficos", "Média, mediana e moda"] },
      { title: "Prática", lessons: ["Dispersão", "Probabilidade básica", "Exercícios de prova"] },
    ],
    lessons: [],
    materials: [],
  },
  {
    id: "redacao-nota-mil",
    image: "/images/courses/redacao-nota-mil.webp",
    subject: "Redação",
    group: "Linguagens",
    title: "Redação nota mil: da tese à conclusão",
    teacher: "Profa. Marina Lopes",
    lessonCount: 20,
    duration: "18h 40min",
    rating: 4.9,
    exams: ["ENEM"],
    summary: "Construa argumentos consistentes e pratique cada etapa do texto dissertativo.",
    audience: "Estudantes que querem planejar e escrever redações dissertativas com mais segurança.",
    access: "paid",
    price: 34.9,
    status: "Publicado",
    studentCount: 7100,
    syllabus: [
      { title: "Planejamento", lessons: ["Leitura do tema", "Tese e repertório", "Projeto de texto"] },
      { title: "Escrita", lessons: ["Desenvolvimento", "Conclusão", "Revisão orientada"] },
    ],
    lessons: [],
    materials: [],
  },
  {
    id: "quimica-organica",
    image: "/images/courses/quimica-organica.webp",
    subject: "Química",
    group: "Ciências da Natureza",
    title: "Química Orgânica sem mistério",
    teacher: "Prof. Lucas Ribeiro",
    lessonCount: 31,
    duration: "29h 10min",
    rating: 4.7,
    exams: ["ENEM", "FUVEST"],
    summary: "Aprenda funções orgânicas, reações e aplicações presentes no cotidiano.",
    audience: "Estudantes que buscam uma introdução objetiva à química orgânica para vestibulares.",
    access: "paid",
    price: 27.9,
    status: "Publicado",
    studentCount: 5900,
    syllabus: [
      { title: "Funções orgânicas", lessons: ["Hidrocarbonetos", "Funções oxigenadas", "Funções nitrogenadas"] },
      { title: "Reações", lessons: ["Principais mecanismos", "Polímeros", "Questões comentadas"] },
    ],
    lessons: [],
    materials: [],
  },
  {
    id: "historia-brasil",
    image: "/images/courses/historia-brasil.webp",
    subject: "História",
    group: "Ciências Humanas",
    title: "História do Brasil em perspectiva",
    teacher: "Prof. André Nascimento",
    lessonCount: 26,
    duration: "22h 30min",
    rating: 4.8,
    exams: ["ENEM", "UNICAMP"],
    summary: "Relacione os principais períodos da história brasileira a seus contextos sociais.",
    audience: "Estudantes que querem revisar História do Brasil conectando eventos e contextos.",
    access: "free",
    price: 0,
    status: "Publicado",
    studentCount: 9700,
    syllabus: [
      { title: "Brasil colonial", lessons: ["Colonização", "Economia açucareira", "Mineração"] },
      { title: "Brasil contemporâneo", lessons: ["Império", "República", "Questões interdisciplinares"] },
    ],
    lessons: [],
    materials: [],
  },
];

export function findDemoCourse(id: string) {
  return demoCourses.find((course) => course.id === id);
}
