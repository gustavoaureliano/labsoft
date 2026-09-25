import styles from "./ProgressBar.module.css";

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className={styles.track} role="progressbar" aria-label="Progresso do curso" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <span style={{ width: `${value}%` }} />
    </div>
  );
}
