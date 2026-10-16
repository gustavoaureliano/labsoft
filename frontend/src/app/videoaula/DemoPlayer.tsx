"use client";

import Image from "next/image";
import { useState } from "react";
import styles from "./page.module.css";

export function DemoPlayer({ lessonId, thumbnail }: { lessonId: string; thumbnail: string }) {
  const [player, setPlayer] = useState({ lessonId, playing: false });
  const playing = player.lessonId === lessonId ? player.playing : false;

  function togglePlaying() {
    setPlayer((current) => ({ lessonId, playing: current.lessonId === lessonId ? !current.playing : true }));
  }

  return (
    <div className={styles.player}>
      <Image alt="" fill priority sizes="(max-width: 1050px) 100vw, 70vw" src={thumbnail} />
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
