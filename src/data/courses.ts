export type EnrolledLesson = {
  id: string;
  number: string;
  title: string;
  duration: string;
  status: "Concluída" | "Aula atual" | "Próxima aula";
  description: string;
};

const lessons: EnrolledLesson[] = [
  { id: "grandezas-vetores", number: "01", title: "Grandezas e vetores", duration: "18 min", status: "Concluída", description: "Revise grandezas escalares, vetoriais e suas representações." },
  { id: "movimento-uniforme", number: "02", title: "Movimento uniforme", duration: "22 min", status: "Concluída", description: "Entenda velocidade constante e interprete gráficos de movimento." },
  { id: "movimento-variado", number: "03", title: "Movimento uniformemente variado", duration: "26 min", status: "Concluída", description: "Relacione aceleração, velocidade e posição em movimentos variados." },
  { id: "queda-livre", number: "04", title: "Queda livre", duration: "19 min", status: "Concluída", description: "Aplique as equações do movimento à queda dos corpos." },
  { id: "lancamentos", number: "05", title: "Lançamentos vertical e oblíquo", duration: "28 min", status: "Concluída", description: "Analise lançamentos decompondo o movimento em seus eixos." },
  { id: "movimento-aceleracao", number: "06", title: "Movimento e aceleração", duration: "21 min", status: "Concluída", description: "Consolide a relação entre movimento, velocidade e aceleração." },
  { id: "introducao-forcas", number: "07", title: "Introdução às forças", duration: "20 min", status: "Concluída", description: "Reconheça as principais forças presentes em problemas de mecânica." },
  { id: "leis-newton", number: "08", title: "Leis de Newton e suas aplicações", duration: "24 min", status: "Aula atual", description: "Entenda as três leis de Newton e veja como elas ajudam a explicar situações do dia a dia." },
  { id: "exercicios-dinamica", number: "09", title: "Exercícios de dinâmica", duration: "30 min", status: "Próxima aula", description: "Resolva problemas de força resultante e movimento." },
  { id: "trabalho-energia", number: "10", title: "Trabalho e energia", duration: "25 min", status: "Próxima aula", description: "Relacione trabalho mecânico, energia e potência." },
  { id: "impulso-quantidade", number: "11", title: "Impulso e quantidade de movimento", duration: "23 min", status: "Próxima aula", description: "Estude colisões, impulso e conservação da quantidade de movimento." },
  { id: "revisao-mecanica", number: "12", title: "Revisão de mecânica", duration: "32 min", status: "Próxima aula", description: "Revise os conceitos do curso com questões de vestibular." },
];

export const enrolledCourse = {
  id: "fisica-enem-mecanica",
  image: "/images/courses/fisica-mecanica.webp",
  category: "Física",
  title: "Física para o ENEM: Mecânica",
  teacher: "Prof. Marcelo Andrade",
  teacherInitials: "MA",
  summary: "Aprenda cinemática, dinâmica e energia com foco nas situações mais frequentes do ENEM.",
  totalLessons: lessons.length,
  progress: 68,
  currentLessonId: "leis-newton",
  lessons,
  modules: [
    { title: "Cinemática", lessonIds: lessons.slice(0, 6).map((lesson) => lesson.id) },
    { title: "Dinâmica e energia", lessonIds: lessons.slice(6).map((lesson) => lesson.id) },
  ],
};

export const currentLesson = lessons.find((lesson) => lesson.id === enrolledCourse.currentLessonId)!;

export function findEnrolledLesson(id?: string) {
  return enrolledCourse.lessons.find((lesson) => lesson.id === id) ?? currentLesson;
}

export type LessonCollectionContext =
  | { origin: "course" }
  | { origin: "history" | "favorites" }
  | { origin: "playlist"; playlistId: string };

export function lessonsFromIds(ids: string[]) {
  return ids.flatMap((id) => {
    const lesson = enrolledCourse.lessons.find((item) => item.id === id);
    return lesson ? [lesson] : [];
  });
}

export function lessonHref(lessonId: string, context: LessonCollectionContext = { origin: "course" }) {
  const params = new URLSearchParams({ curso: enrolledCourse.id, aula: lessonId });
  if (context.origin !== "course") params.set("origem", context.origin);
  if (context.origin === "playlist") params.set("lista", context.playlistId);
  return `/videoaula?${params.toString()}`;
}

export function questionHref(lessonId?: string) {
  const params = new URLSearchParams({ curso: enrolledCourse.id });
  if (lessonId) params.set("aula", lessonId);
  return `/duvidas?${params.toString()}`;
}
