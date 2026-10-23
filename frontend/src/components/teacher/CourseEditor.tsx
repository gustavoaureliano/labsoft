"use client";

import { useState, type ChangeEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { blankTeacherCourse, initialTeacherCourses, teacherCoursesKey, type TeacherCourse } from "@/data/teacherCourses";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { DemoFileField } from "./DemoFileField";
import { DemoLessonDrafts } from "./DemoLessonDrafts";
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
  const updateMaterial = (index: number, field: "title" | "kind", value: string) => setCourse((current) => ({ ...current, materials: current.materials.map((material, position) => position === index ? { ...material, [field]: value } : material) }));


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
        <div><span>Editor de cursos</span><h1>{isNew ? "Criar curso" : "Editar informações do curso"}</h1><p>Organize a apresentação e os materiais do curso.</p></div>
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

      {isNew || initialCourse.id.startsWith("curso-") ? <DemoLessonDrafts lessons={course.lessons} image={course.image} onChange={lessons => setCourse(current => ({...current, lessons}))} /> : <section className={styles.card}><div className={styles.sectionHeading}><div><h2>2. Conteúdo das aulas</h2><p>Edite vídeos, imagens e a sequência das aulas em um espaço próprio.</p></div><Link className={styles.primary} href={`/professor/cursos/${initialCourse.id}/aulas`}>Gerenciar aulas</Link></div></section>}

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
