import Image from "next/image";
import styles from "./ProfileLogo.module.css";

export function ProfileLogo() {
  return <Image alt="AprovaAí" className={styles.logo} height={70} src="/aprova-ai-logo.svg" width={280} />;
}
