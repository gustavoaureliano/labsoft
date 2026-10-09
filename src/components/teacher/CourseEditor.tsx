"use client";

import { useState, type ChangeEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { blankTeacherCourse, initialTeacherCourses, teacherCoursesKey, type TeacherCourse } from "@/data/teacherCourses";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { DemoFileField } from "./DemoFileField";
import { DemoImageField } from "./DemoImageField";
import styles from "./CourseEditor.module.css";

export function CourseEditor({ courseId }: { courseId?: string }) {
  const [courses, saveCourses, ready] = useDemoStorage(teacherCoursesKey, initialTeacherCourses);
  if (!ready) return <p>Carregando editor...</p>;

  const course = courseId ? courses.find((item) => item.id === courseId) ?? initialTeacherCourses.find((item) => item.id === courseId) : undefined;
  if (courseId && !course) return <div className={styles.empty}><h1>Curso não encontrado</h1><Link href="/professor/cursos">Voltar para meus cursos</Link></div>;
  return <CourseEditorForm initialCourse={course ?? blankTeacherCourse()} courses={courses} saveCourses={saveCourses} isNew={!courseId} />;
}

function CourseEditorForm({ initialCourse, courses, saveCourses, isNew }: { initialCourse: TeacherCourse; courses: TeacherCourse[]; saveCourses: (courses: TeacherCourse[]) => boolean; isNew: boolean }) {
  const router = useRouter();
  const [course, setCourse] = useState(initialCourse);
  const [preview, setPreview] = useState(false);
  const [notice, setNotice] = useState("");

  const update = (field: keyof TeacherCourse) => (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => setCourse((current) => ({ ...current, [field]: event.target.value }));
  const updateLesson = (index: number, field: "title" | "duration", value: string) => setCourse((current) => ({ ...current, lessons: current.lessons.map((lesson, position) => position === index ? { ...lesson, [field]: value } : lesson) }));
  const updateMaterial = (index: number, field: "title" | "kind", value: string) => setCourse((current) => ({ ...current, materials: current.materials.map((material, position) => position === index ? { ...material, [field]: value } : material) }));

  function moveLesson(index: number, direction: -1 | 1) {
    const destination = index + direction;
    if (destination < 0 || destination >= course.lessons.length) return;
    const lessons = [...course.lessons];
    [lessons[index], lessons[destination]] = [lessons[destination], lessons[index]];
    setCourse((current) => ({ ...current, lessons }));
  }

  function setLessonVideo(index: number, file: { name: string; type: string; size: number } | null) {
    setCourse((current) => ({ ...current, lessons: current.lessons.map((lesson, position) => position === index ? { ...lesson, videoName: file?.name ?? "", videoType: file?.type, videoSize: file?.size } : lesson) }));
  }

  function setLessonThumbnail(index: number, file: { name: string; type: string; size: number } | null) {
    setCourse((current) => ({ ...current, lessons: current.lessons.map((lesson, position) => position === index ? { ...lesson, thumbnail: undefined, thumbnailName: file?.name, thumbnailType: file?.type, thumbnailSize: file?.size } : lesson) }));
  }

  function addMaterial(file: { name: string; type: string; size: number }) {
    const title = file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ");
    const extension = file.name.includes(".") ? file.name.split(".").pop()!.toUpperCase() : "Arquivo";
    setCourse((current) => ({ ...current, materials: [...current.materials, { id: `material-${Date.now()}`, title, kind: extension, fileName: file.name, fileType: file.type, fileSize: file.size }] }));
  }

  function save(status: TeacherCourse["status"]) {
    if (!course.title.trim() || !course.subject.trim() || !course.summary.trim()) {
      setNotice("Preencha título, matéria e descrição antes de salvar.");
      return;
    }
    const id = course.id || `curso-${Date.now()}`;
    const saved = { ...course, id, status, price: course.access === "free" ? "0,00" : course.price };
    saveCourses(isNew ? [...courses, saved] : courses.map((item) => item.id === saved.id ? saved : item));
    router.push("/professor/cursos?salvo=1");
  }

  return (
    <div className={styles.editor}>
      <header className={styles.heading}>
        <div><span>Editor de cursos</span><h1>{isNew ? "Criar curso" : "Editar curso"}</h1><p>Organize as informações e o conteúdo antes de publicar.</p></div>
        <Link href="/professor/cursos">Cancelar e voltar</Link>
      </header>

      <section className={styles.card} aria-labelledby="information-title">
        <h2 id="information-title">1. Informações do curso</h2>
        <div className={styles.formGrid}>
          <label className={styles.full}>Título<input name="title" value={course.title} onChange={update("title")} required /></label>
          <label>Matéria<input name="subject" value={course.subject} onChange={update("subject")} required /></label>
          <label>Vestibulares<input name="exams" value={course.exams} onChange={update("exams")} placeholder="ENEM, FUVEST" /></label>
          <label className={styles.full}>Descrição<textarea name="summary" rows={4} value={course.summary} onChange={update("summary")} required /></label>
          <label>Forma de acesso<select name="access" value={course.access} onChange={update("access")}><option value="free">Gratuito</option><option value="paid">Pago</option></select></label>
          <label>Preço<input name="price" value={course.price} onChange={update("price")} disabled={course.access === "free"} /></label>
        </div>
      </section>

      <section className={styles.card} aria-labelledby="lessons-title">
        <div className={styles.sectionHeading}><div><h2 id="lessons-title">2. Aulas</h2><p>Selecione um vídeo real. Somente seus dados serão mantidos nesta demonstração.</p></div><button type="button" onClick={() => setCourse((current) => ({ ...current, lessons: [...current.lessons, { id: `aula-${Date.now()}`, title: "", duration: "", videoName: "" }] }))}>+ Adicionar aula</button></div>
        <div className={styles.rows}>{course.lessons.length ? course.lessons.map((lesson, index) => <div className={styles.contentRow} key={lesson.id}>
          <span className={styles.position}>{index + 1}</span>
          <label>Título<input aria-label={`Título da aula ${index + 1}`} value={lesson.title} onChange={(event) => updateLesson(index, "title", event.target.value)} /></label>
          <label>Duração<input aria-label={`Duração da aula ${index + 1}`} value={lesson.duration} onChange={(event) => updateLesson(index, "duration", event.target.value)} placeholder="20 min" /></label>
          <div className={styles.mediaFields}>
            <div className={styles.videoField}><span>Vídeo</span><DemoFileField accept="video/*" inputLabel={`Selecionar vídeo da aula ${index + 1}`} current={lesson.videoName ? { name: lesson.videoName, type: lesson.videoType ?? "Vídeo", size: lesson.videoSize ?? 0 } : null} onSelect={(file) => setLessonVideo(index, file)} onRemove={() => setLessonVideo(index, null)} /></div>
            <div className={styles.thumbnailField}><span>Thumbnail</span><DemoImageField fallback={lesson.thumbnail ?? course.image} inputLabel={`Selecionar thumbnail da aula ${index + 1}`} current={lesson.thumbnailName ? { name: lesson.thumbnailName, type: lesson.thumbnailType ?? "Imagem", size: lesson.thumbnailSize ?? 0 } : null} onSelect={(file) => setLessonThumbnail(index, file)} onRemove={() => setLessonThumbnail(index, null)} /></div>
          </div>
          <div className={styles.rowActions}><button type="button" disabled={index === 0} aria-label={`Mover aula ${index + 1} para cima`} onClick={() => moveLesson(index, -1)}>↑</button><button type="button" disabled={index === course.lessons.length - 1} aria-label={`Mover aula ${index + 1} para baixo`} onClick={() => moveLesson(index, 1)}>↓</button><button type="button" onClick={() => setCourse((current) => ({ ...current, lessons: current.lessons.filter((_, position) => position !== index) }))}>Excluir</button></div>
        </div>) : <p className={styles.emptyRow}>Nenhuma aula adicionada.</p>}</div>
      </section>

      <section className={styles.card} aria-labelledby="materials-title">
        <div className={styles.sectionHeading}><div><h2 id="materials-title">3. Materiais complementares</h2><p>Envie PDFs, documentos, apresentações ou arquivos compactados.</p></div><DemoFileField accept=".pdf,.doc,.docx,.ppt,.pptx,.zip" inputLabel="Enviar material" onSelect={addMaterial} /></div>
        <div className={styles.rows}>{course.materials.length ? course.materials.map((material, index) => <div className={styles.materialRow} key={material.id}><label>Título<input aria-label={`Título do material ${index + 1}`} value={material.title} onChange={(event) => updateMaterial(index, "title", event.target.value)} /></label><label>Formato<select aria-label={`Formato do material ${index + 1}`} value={material.kind} onChange={(event) => updateMaterial(index, "kind", event.target.value)}><option>PDF</option><option>DOC</option><option>DOCX</option><option>PPT</option><option>PPTX</option><option>ZIP</option><option>Link</option></select></label><div className={styles.materialFile}><span>{material.fileName ?? material.title}</span><small>{material.fileType || material.kind}{material.fileSize ? ` · ${(material.fileSize / 1024).toFixed(0)} KB` : ""}</small></div><button type="button" onClick={() => setCourse((current) => ({ ...current, materials: current.materials.filter((_, position) => position !== index) }))}>Excluir</button></div>) : <p className={styles.emptyRow}>Nenhum material adicionado.</p>}</div>
      </section>

      {preview && <section className={styles.preview} aria-label="Prévia do curso"><span>Prévia</span><h2>{course.title || "Curso sem título"}</h2><p>{course.summary || "Adicione uma descrição para apresentar o curso."}</p><strong>{course.lessons.length} {course.lessons.length === 1 ? "aula" : "aulas"} · {course.access === "free" ? "Gratuito" : `R$ ${course.price}`}</strong></section>}
      {notice && <p className={styles.notice} role="status">{notice}</p>}
      <div className={styles.footerActions}><button className={styles.secondary} type="button" onClick={() => setPreview((current) => !current)}>{preview ? "Fechar prévia" : "Visualizar prévia"}</button><button className={styles.secondary} type="button" onClick={() => save("Rascunho")}>Salvar rascunho</button><button className={styles.primary} type="button" onClick={() => save("Publicado")}>Publicar curso</button></div>
    </div>
  );
}
