import type { SVGProps } from "react";

type IconName = "home" | "book" | "search" | "award" | "user" | "chevron" | "check" | "menu";

export function Icon({ name, ...props }: SVGProps<SVGSVGElement> & { name: IconName }) {
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const paths: Record<IconName, React.ReactNode> = {
    home: <><path d="m2 11 10-9 10 9v10a1 1 0 0 1-1 1h-6v-7H9v7H3a1 1 0 0 1-1-1z" /></>,
    book: <><path d="M12 6c-3-2-6-2-9-1v14c3-1 6-1 9 1 3-2 6-2 9-1V5c-3-1-6-1-9 1z" /><path d="M12 6v14" /></>,
    search: <><circle cx="10.8" cy="10.8" r="6.7" /><path d="m16 16 5 5" /></>,
    award: <><circle cx="12" cy="8" r="5" /><path d="m8 12-1 9 5-3 5 3-1-9" /></>,
    user: <><circle cx="12" cy="8" r="4" /><path d="M4 21c.5-4.5 3.2-7 8-7s7.5 2.5 8 7" /></>,
    chevron: <path d="m6 9 6 6 6-6" />,
    check: <path d="m5 12 4 4L19 6" />,
    menu: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
  };
  return <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" {...common} {...props}>{paths[name]}</svg>;
}
