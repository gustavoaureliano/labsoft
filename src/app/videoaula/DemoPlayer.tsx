"use client";

import { useState } from "react";
import styles from "./page.module.css";

export function DemoPlayer({ lessonId }: { lessonId: string }) {
  const [player, setPlayer] = useState({ lessonId, playing: false });
  const playing = player.lessonId === lessonId ? player.playing : false;

  function togglePlaying() {
    setPlayer((current) => ({ lessonId, playing: current.lessonId === lessonId ? !current.playing : true }));
  }

  return (
    <div className={styles.player}>
      <button
        aria-label={playing ? "Pausar demonstração" : "Reproduzir demonstração"}
        aria-pressed={playing}
        className={styles.playIcon}
        onClick={togglePlaying}
        type="button"
      >
        <span aria-hidden="true">{playing ? "❚❚" : "▶"}</span>
      </button>
      <strong>Área da videoaula</strong>
      <span>O vídeo será adicionado em breve.</span>
    </div>
  );
}
