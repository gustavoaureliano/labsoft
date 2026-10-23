import Image from "next/image";
import styles from "./Avatar.module.css";

export function Avatar({ size = "small", image }: { size?: "small" | "large"; image?: string | null }) {
  return <span className={`${styles.avatar} ${styles[size]}`}>
    {image
      ? <Image src={image} alt="Avatar do estudante" width={size === "large" ? 76 : 34} height={size === "large" ? 76 : 34} unoptimized />
      : <span className={styles.referenceArt} role="img" aria-label="Avatar ilustrado do estudante" />}
  </span>;
}
