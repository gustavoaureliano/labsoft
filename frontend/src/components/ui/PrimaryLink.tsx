import Link from "next/link";
import styles from "./PrimaryLink.module.css";

export function PrimaryLink({ href, children, className = "" }: { href: string; children: React.ReactNode; className?: string }) {
  return <Link className={`${styles.link} ${className}`} href={href}>{children}</Link>;
}
