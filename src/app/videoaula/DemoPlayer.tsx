"use client";

import { useState } from "react";
import Image from "next/image";
import styles from "./page.module.css";

export function DemoPlayer() {
  const [playing, setPlaying] = useState(false);

  return (
    <div className={styles.player}>
      <Image alt="Prévia da videoaula sobre as leis de Newton" fill priority sizes="(max-width: 1050px) 100vw, 70vw" src="/images/video/leis-de-newton.png" />
      <button
        aria-label={playing ? "Pausar demonstração" : "Reproduzir demonstração"}
        aria-pressed={playing}
        className={styles.playIcon}
        onClick={() => setPlaying((value) => !value)}
        type="button"
      >
        <span aria-hidden="true">{playing ? "❚❚" : "▶"}</span>
      </button>
      <strong>Área da videoaula</strong>
      <span>O vídeo será adicionado em breve.</span>
    </div>
  );
}
