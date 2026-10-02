export type Course = {
  category: string;
  title: string;
  teacher: string;
  duration: string;
  image: string;
};

export const recommendedCourses: Course[] = [
  { category: "Matemática", title: "Funções e gráficos sem mistério", teacher: "Profa. Ana Martins", duration: "18 aulas", image: "/images/courses/matematica-funcoes.png" },
  { category: "Química", title: "Química orgânica essencial", teacher: "Prof. Lucas Ribeiro", duration: "24 aulas", image: "/images/courses/quimica-organica.png" },
  { category: "Física", title: "Eletricidade do zero", teacher: "Prof. Marcelo Andrade", duration: "15 aulas", image: "/images/courses/fisica-eletricidade.png" },
];

export const currentLesson = {
  number: "08",
  title: "Leis de Newton e suas aplicações",
  status: "Aula atual",
  description: "Entenda as três leis de Newton e veja como elas ajudam a explicar situações do dia a dia.",
};

export const enrolledCourse = {
  category: "Física",
  title: "Física para o ENEM: Mecânica",
  image: "/images/courses/fisica-mecanica.png",
  teacher: "Prof. Marcelo Andrade",
  teacherInitials: "MA",
  totalLessons: 12,
  progress: 68,
  currentLessonNumber: currentLesson.number,
  lessons: [
    { number: "06", title: "Movimento e aceleração", status: "Concluída" },
    { number: "07", title: "Introdução às forças", status: "Concluída" },
    currentLesson,
    { number: "09", title: "Exercícios de dinâmica", status: "Próxima aula" },
  ],
};
