import Image from "next/image";
import Link from "next/link";
import styles from "./Logo.module.css";

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link className={styles.logo} href={href} aria-label="Ir para a página inicial da AprovaAí">
      <Image
        alt="AprovaAí"
        className={styles.image}
        height={70}
        priority
        src="/aprova-ai-logo.svg"
        width={280}
      />
    </Link>
  );
}
