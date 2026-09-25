import styles from "./Logo.module.css";

export function Logo() {
  return (
    <div className={styles.logo} aria-label="Logos Academy">
      <span className={styles.mark} aria-hidden="true">
        L
      </span>
      <span className={styles.text}>
        <strong>Logos</strong>
        <small>Academy</small>
      </span>
    </div>
  );
}
