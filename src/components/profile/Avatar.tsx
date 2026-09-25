import styles from "./Avatar.module.css";

export function Avatar({ size = "small", image }: { size?: "small" | "large"; image?: string | null }) {
  return <span className={`${styles.avatar} ${styles[size]}`}>
    {image
      ? <img src={image} alt="Avatar do estudante" />
      : <span className={styles.referenceArt} role="img" aria-label="Avatar ilustrado do estudante" />}
  </span>;
}
