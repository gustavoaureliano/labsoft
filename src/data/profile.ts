export type Profile = {
  nickname: string;
  email: string;
  description: string;
};

export const initialProfile: Profile = {
  nickname: "Bob Silva",
  email: "uzumaki.betinho97@hotmail.com",
  description: "Eu sou o bob, gosto muito de cachorros e de estudar. Quero passar na FUVEST para ser o primeiro astronauta veterinário quântico de paranaipacaba e ajudar todos os cachorros do mundo!",
};

export const navigation = [
  { label: "Início", icon: "home", href: "/" },
  { label: "Meus Cursos", icon: "book", href: "/meus-cursos" },
  { label: "Explorar", icon: "search", href: "/explorar" },
  { label: "Certificados", icon: "award", href: "/certificados" },
  { label: "Perfil", icon: "user", href: "/perfil" },
] as const;
