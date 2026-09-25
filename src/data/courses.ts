export type Course = {
  category: string;
  title: string;
  teacher: string;
  duration: string;
};

export const recommendedCourses: Course[] = [
  { category: "Matemática", title: "Funções e gráficos sem mistério", teacher: "Profa. Ana Martins", duration: "18 aulas" },
  { category: "Química", title: "Química orgânica essencial", teacher: "Prof. Lucas Ribeiro", duration: "24 aulas" },
  { category: "Física", title: "Eletricidade do zero", teacher: "Prof. Marcelo Andrade", duration: "15 aulas" },
];
