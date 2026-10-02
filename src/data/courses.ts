export const currentLesson = {
  number: "08",
  title: "Leis de Newton e suas aplicações",
  status: "Aula atual",
  description: "Entenda as três leis de Newton e veja como elas ajudam a explicar situações do dia a dia.",
};

export const enrolledCourse = {
  category: "Física",
  title: "Física para o ENEM: Mecânica",
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
