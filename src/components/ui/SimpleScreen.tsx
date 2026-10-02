import type { ReactNode } from "react";
import styles from "./SimpleScreen.module.css";

export function SimpleScreen({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children: ReactNode }) {
  return (
    <div className={styles.screen}>
      <header className={styles.header}>
        <span>{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </header>
      {children}
    </div>
  );
}
