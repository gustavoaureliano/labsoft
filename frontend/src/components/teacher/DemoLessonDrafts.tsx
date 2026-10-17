"use client";

import { DemoFileField } from "./DemoFileField";
import { DemoImageField } from "./DemoImageField";
import type { TeacherLesson } from "@/data/teacherCourses";
import styles from "./CourseEditor.module.css";

// Course creation is still another domain's local demo. Do not pretend that
// these draft lessons were uploaded to the API before a real course exists.
export function DemoLessonDrafts({lessons, image, onChange}: {lessons: TeacherLesson[]; image: string; onChange: (lessons: TeacherLesson[]) => void}) {
  function update(index: number, changes: Partial<TeacherLesson>) {
    onChange(lessons.map((lesson, position) => position === index ? {...lesson, ...changes} : lesson));
  }
  return <section className={styles.card} aria-labelledby="lessons-title">
    <div className={styles.sectionHeading}><div><h2 id="lessons-title">2. Aulas demonstrativas do novo curso</h2><p>Este curso ainda não existe no backend. Os arquivos abaixo guardam apenas metadados no navegador.</p></div><button type="button" onClick={() => onChange([...lessons, {id: crypto.randomUUID(), title: "", duration: "", videoName: ""}])}>+ Adicionar aula</button></div>
    {lessons.map((lesson, index) => <div className={styles.contentRow} key={lesson.id}>
      <span>{index + 1}</span><label>Título<input aria-label={`Título da aula ${index + 1}`} value={lesson.title} onChange={event => update(index, {title: event.target.value})} /></label>
      <label>Duração<input aria-label={`Duração da aula ${index + 1}`} value={lesson.duration} onChange={event => update(index, {duration: event.target.value})} /></label>
      <DemoFileField accept="video/*" inputLabel={`Selecionar vídeo da aula ${index + 1}`} current={lesson.videoName ? {name: lesson.videoName, type: lesson.videoType ?? "Vídeo", size: lesson.videoSize ?? 0} : null} onSelect={file => update(index, {videoName: file.name, videoType: file.type, videoSize: file.size})} onRemove={() => update(index, {videoName: ""})} />
      <DemoImageField fallback={lesson.thumbnail ?? image} inputLabel={`Selecionar thumbnail da aula ${index + 1}`} current={lesson.thumbnailName ? {name: lesson.thumbnailName, type: lesson.thumbnailType ?? "Imagem", size: lesson.thumbnailSize ?? 0} : null} onSelect={file => update(index, {thumbnailName: file.name, thumbnailType: file.type, thumbnailSize: file.size})} onRemove={() => update(index, {thumbnailName: undefined})} />
      <div className={styles.rowActions}><button type="button" disabled={index === 0} onClick={() => {const next = [...lessons]; [next[index - 1], next[index]] = [next[index], next[index - 1]]; onChange(next);}}>↑</button><button type="button" disabled={index === lessons.length - 1} onClick={() => {const next = [...lessons]; [next[index], next[index + 1]] = [next[index + 1], next[index]]; onChange(next);}}>↓</button><button type="button" onClick={() => onChange(lessons.filter(item => item.id !== lesson.id))}>Excluir</button></div>
    </div>)}
  </section>;
}
