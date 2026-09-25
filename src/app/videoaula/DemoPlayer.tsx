"use client";

import { useState } from "react";
import styles from "./page.module.css";

export function DemoPlayer() {
  const [playing, setPlaying] = useState(false);

  return (
    <div className={styles.player}>
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
