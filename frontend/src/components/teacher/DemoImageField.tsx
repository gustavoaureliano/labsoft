"use client";

import Image from "next/image";
import { useEffect, useRef, useState, type ChangeEvent } from "react";
import type { DemoFileMetadata } from "@/data/teacherCourses";
import styles from "./DemoImageField.module.css";

export function DemoImageField({ current, fallback, inputLabel, onRemove, onSelect }: { current?: DemoFileMetadata | null; fallback: string; inputLabel: string; onRemove: () => void; onSelect: (file: DemoFileMetadata) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview);
  }, [preview]);

  function chooseImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setNotice("Escolha um arquivo de imagem.");
      event.target.value = "";
      return;
    }
    setPreview(URL.createObjectURL(file));
    onSelect({ name: file.name, type: file.type || "Imagem", size: file.size });
    setNotice("");
    event.target.value = "";
  }

  function removeImage() {
    setPreview("");
    setNotice("");
    onRemove();
  }

  return (
    <div className={styles.field}>
      <input ref={input} className={styles.input} type="file" accept="image/png,image/jpeg,image/webp" aria-label={inputLabel} onChange={chooseImage} />
      <div className={styles.preview}><Image alt="" fill sizes="112px" src={preview || fallback} unoptimized={Boolean(preview)} /></div>
      <div className={styles.details}>
        <strong>{current?.name || "Capa do curso usada como padrão"}</strong>
        <small>{current?.name ? "A imagem escolhida é demonstrativa e a prévia fica disponível até sair desta tela." : "Envie uma imagem PNG, JPEG ou WebP em formato 16:9."}</small>
        <div className={styles.actions}>
          <button type="button" onClick={() => input.current?.click()}>{current?.name ? "Trocar" : "Selecionar thumbnail"}</button>
          {current?.name && <button type="button" onClick={removeImage}>Remover</button>}
        </div>
      </div>
      {notice && <small className={styles.notice} role="status">{notice}</small>}
    </div>
  );
}
