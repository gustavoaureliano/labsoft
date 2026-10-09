// TODO: A gente precisa definir um schema....
// Acho que eu acabei exagerando :/


export type ProgramItem = {
  id: string;
  name: string;
  length: number; // minutes
}

export enum ProgramItemState {
  NOT_STARTED,
  IN_PROGRESS,
  FINISHED,
}


export type ProgramItemProgress ={
  id: string;
  state: ProgramItemState;
  timestamp: number | null ;
}

export default enum EnrollmentStatus {
  ENROLLED,
  NOT_ENROLLED,
  FINISHED
}

export type CourseEnrollment = {
  userId: string;
  courseId: string;
  status: EnrollmentStatus;
  programItems:  ProgramItemProgress[];
}


export type Teacher ={
  id: string;
  name: string;
  gender: string;
  treatment: string;
  role: string;
  rating: number;
  about: string;
}


export type Course = {
  id: string;
  title: string;
  summary: string;
  category: string;
  about: string;
  rating: string;
  defaultThumbnail: string;
  lessonCount: number;
  studentCount: number;
  totalDuration: number;
  teacherId: string ;
  program: ProgramItem[];  
  includes: string[];
}



export const incluso: string[] = [
    "42 videoaulas", "Exercícios comentados",
    "Materiais complementares", "Certificado de conclusão",
    "Fórum direto com o professor"
];


const programa: ProgramItem[] = [
  { id: "p1", name: "Introdução e contexto histórico", length: 48 },
  { id: "p2", name: "Radiação de corpo negro e a hipótese de Plank", length: 56 },
  { id: "p3", name: "Efeito fotoeletrico", length: 65 },
  { id: "p4", name: "Dualidade onda-particula", length: 52 }
];


export const fulano: Teacher = {
  id: "t1",
  name: "Fulano da Silva",
  gender: "male",
  treatment: "Prof.",
  role: "Professor de Física",
  rating: 4.9,
  about: "Especialista para FUVEST, ENEM e UNICAMP."
}


const fisica: Course = {
  id: "fisica-quantica",
  title: "Introducao à Física Quântica",
  summary: "Compreenda os fundamentos da física moderna com uma abordagem clara, aplicada às principais provas de vestibular.",
  about: "O curso apresenta conceitos de quantização, dualidade onda-partícula e estrutura atômica com exemplos resolvidos e exercícios no formato dos vestibulares paulistas.",
  category: "FÍSICA • FUVEST",
  rating: 5.0,
  teacherId: "t1",
  program: programa,
  lessonCount: programa.length,
  studentCount: 12.420,
  totalDuration: programa.reduce((a, i) => {return a + i.length}),
    defaultThumbnail: "https://i.ytimg.com/an_webp/0Ayx7CYyxTY/mqdefault_6s.webp?du=3000&sqp=CLL9oNYG&rs=AOn4CLBXq6cut2O8PyNSsLCi8GA_wREceQ",
  includes: incluso
}



export interface iCtx {
  getUser(): string;
}

export const mockCtx = {
  getUser(): string{
    return "u1";
  }
}
/*
export const estadoPrograma: ProgramItemStatus[]{
  { "p1", FINISHED, null },
  { "p2", FINISHED, null },
  { "p3", IN_PROGRESS, 65 },
  { "p4", NOT_STARTED, null }
}
*/

export interface iORM {
  getTeacherById(id: string): Teacher | null;
  getCourseById(id: string): Course | null;
  getEnrollmentInfo(courseId: string, userId:string): CourseEnrollment | null;
}

export const mockOrm: iORM = {

  getCourseById(id: string): Course | null {
    if(id === "fisica-quantica"){
      return fisica;
    }
    return null;
  },


  getEnrollmentInfo(courseId: string, userId: string): Course | null {
    if (userId === "u1" && courseId === "fisica-quantica" ){
      return {
        userId: "u1", courseId: "fisica-quantica", status: EnrollmntStatus.ENROLLED, 
        programItems: estadoPrograma
      }
    return null;
    };
  },

  getTeacherById(id: string): Teacher | null {
    if(id=="t1"){
      return fulano;
    }
    return null;
  }

};


export const mockCourseEnrolled ={
  id: "fisica-quantica",
  enrollment: EnrollmentStatus.ENROLLED,
  title: "Introducao à Física Quântica",
  summary: "Compreenda os fundamentos da física moderna com uma abordagem clara, aplicada às principais provas de vestibular.",
  about: "O curso apresenta conceitos de quantização, dualidade onda-partícula e estrutura atômica com exemplos resolvidos e exercícios no formato dos vestibulares paulistas.",
  category: "FÍSICA • FUVEST",
  rating: 5.0,
  teacher: {
    id: "t1",
    name: "Fulano da Silva",
    gender: "male",
    treatment: "Prof.",
    role: "Professor de Física",
    rating: 4.9,
    about: "Especialista para FUVEST, ENEM e UNICAMP."
  },
  program: [
    { id: "p1", name: "Introdução e contexto histórico", 
      length: 48, state: ProgramItemState.IN_PROGRESS, timestamp: 40 },
    { id: "p2", name: "Radiação de corpo negro e a hipótese de Plank",
      length: 56, state: ProgramItemState.FINISHED, timestamp: null },
    { id: "p3", name: "Efeito fotoeletrico", length: 65,
      state: ProgramItemState.IN_PROGRESS, timestamp: 4},
    { id: "p4", name: "Dualidade onda-particula", 
      lentgh: 52, state: ProgramItemState.NOT_STARTED, timestamp : 0 }
  ],
  lessonCount: 42,
  nextItem: {
    id: "id", name: "Introdução e contexto histórico"
  },
  studentCount: 12420,
  totalDuration: 3024,
  thumbnail: "https://i.ytimg.com/vi/eA1E2HGdbKg/hq720.jpg?sqp=-oaymwEcCNAFEJQDSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLCz6NuqOfwuVDXOFO9N4ITrA0zG0Q",
    includes: [
    "42 videoaulas", "Exercícios comentados",
    "Materiais complementares", "Certificado de conclusão",
    "Fórum direto com o professor"
  ]
}

export const mockCourseNotEnrolled = {

        id: "fisica-quantica",
        enrollment: EnrollmentStatus.NOT_ENROLLED,
        price: 76.00,
        title: "Introducao à Física Quântica",
        summary: "Compreenda os fundamentos da física moderna com uma abordagem clara, aplicada às principais provas de vestibular.",
        about: "O curso apresenta conceitos de quantização, dualidade onda-partícula e estrutura atômica com exemplos resolvidos e exercícios no formato dos vestibulares paulistas.",
        category: "FÍSICA • FUVEST",
        rating: 5.0,
        teacher: {
          id: "t1",
          name: "Fulano da Silva",
          gender: "male",
          treatment: "Prof.",
          role: "Professor de Física",
          rating: 4.9,
          about: "Especialista para FUVEST, ENEM e UNICAMP."
        },
        program: [
            { id: "p1", name: "Introdução e contexto histórico", length: 48},
            { id: "p2", name: "Radiação de corpo negro e a hipótese de Plank", length: 56},
            { id: "p3", name: "Efeito fotoeletrico", length: 65 },
            { id: "p4", name: "Dualidade onda-particula", lentgh: 52 }
        ],
        lessonCount: 42,
        studentCount: 12420,
        totalDuration: 3024,
        thumbnail: "https://i.ytimg.com/an_webp/0Ayx7CYyxTY/mqdefault_6s.webp?du=3000&sqp=CLL9oNYG&rs=AOn4CLBXq6cut2O8PyNSsLCi8GA_wREceQ",
        includes: [
            "42 videoaulas", "Exercícios comentados",
            "Materiais complementares", "Certificado de conclusão",
            "Fórum direto com o professor"
        ]
};
