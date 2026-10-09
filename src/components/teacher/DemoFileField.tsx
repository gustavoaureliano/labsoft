"use client";

import { useRef, useState, type ChangeEvent } from "react";
import type { DemoFileMetadata } from "@/data/teacherCourses";
import styles from "./DemoFileField.module.css";

function formatSize(size?: number) {
  if (!size) return "arquivo demonstrativo";
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`;
  return `${(size / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`;
}

export function DemoFileField({ accept, current, inputLabel, onRemove, onSelect }: { accept: string; current?: DemoFileMetadata | null; inputLabel: string; onRemove?: () => void; onSelect: (file: DemoFileMetadata) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [notice, setNotice] = useState("");

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (accept === "video/*" && !file.type.startsWith("video/")) {
      setNotice("Escolha um arquivo de vídeo.");
      event.target.value = "";
      return;
    }
    onSelect({ name: file.name, type: file.type || "Arquivo", size: file.size });
    setNotice("");
    event.target.value = "";
  }

  return (
    <div className={styles.field}>
      <input ref={input} className={styles.input} type="file" accept={accept} aria-label={inputLabel} onChange={chooseFile} />
      {current?.name ? <div className={styles.file}><div><strong>{current.name}</strong><small>{current.type || "Arquivo"} · {formatSize(current.size)}</small></div><div className={styles.actions}><button type="button" onClick={() => input.current?.click()}>Trocar</button>{onRemove && <button type="button" onClick={onRemove}>Remover</button>}</div></div> : <button className={styles.select} type="button" onClick={() => input.current?.click()}>{inputLabel}</button>}
      {notice && <small className={styles.notice} role="status">{notice}</small>}
    </div>
  );
}
