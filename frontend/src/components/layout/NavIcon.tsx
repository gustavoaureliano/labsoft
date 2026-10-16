export type NavIconName = "home" | "courses" | "doubts" | "explore" | "materials" | "certificates" | "profile" | "help" | "collapse" | "expand";

const paths: Record<NavIconName, string> = {
  home: "M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3V10.5Z",
  courses: "M4 4h16v16H4V4Zm4 4h8M8 12h8M8 16h5",
  doubts: "M4 4h16v14H8l-4 3V4Zm5 5h6m-6 4h6",
  explore: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm3 7-2 5-4 1 2-5 4-1Z",
  materials: "M6 3h9l4 4v14H6V3Zm9 0v5h4M9 12h7m-7 4h7",
  certificates: "m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z",
  profile: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-8 9v-2a8 8 0 0 1 16 0v2H4Z",
  help: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm-3 7a3 3 0 0 1 6 0c0 2-3 2-3 4m0 3h.01",
  collapse: "m15 6-6 6 6 6",
  expand: "m9 6 6 6-6 6",
};

export function NavIcon({ name }: { name: NavIconName }) {
  return <svg aria-hidden="true" fill="none" height="20" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" viewBox="0 0 24 24" width="20"><path d={paths[name]} /></svg>;
}
