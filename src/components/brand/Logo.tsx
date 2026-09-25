import Link from "next/link";
import styles from "./Logo.module.css";

export function Logo() {
  return (
    <Link className={styles.logo} href="/" aria-label="Ir para a página inicial">
      <span className={styles.mark} aria-hidden="true">
        L
      </span>
      <span className={styles.text}>
        <strong>Logos</strong>
        <small>Academy</small>
      </span>
    </Link>
  );
}
