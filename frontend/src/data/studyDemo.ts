export const studyDemoKey = "aprovaai-demo-study";

export type StudyDemo = {
  viewedLessons: string[];
  favoriteLessons: string[];
  playlists: { id: string; name: string; lessonIds: string[] }[];
};

export const initialStudyDemo: StudyDemo = {
  viewedLessons: [],
  favoriteLessons: [],
  playlists: [{ id: "revisao-enem", name: "Revisão ENEM", lessonIds: [] }],
};
