"use client";

import { useEffect, useState, type ChangeEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { blankTeacherCourse, type TeacherCourse } from "@/data/teacherCourses";
import { apiErrorMessage, apiRequest, teacherHeaders } from "@/lib/api/client";
import type { ApiCourse, ApiCoursePreview, ApiLesson, ApiMaterial } from "@/lib/api/types";
import { DemoFileField } from "./DemoFileField";
import { DemoImageField } from "./DemoImageField";
import styles from "./CourseEditor.module.css";

const fallbackCover = "/images/courses/fisica-quantica.webp";

function previewToEditor(preview: ApiCoursePreview): TeacherCourse {
  return {
    id: preview.course.id,
    title: preview.course.title,
    subject: preview.course.subject,
    summary: preview.course.summary,
    exams: preview.course.exams.join(", "),
    access: preview.course.access_type,
    price: Number(preview.course.price ?? 0).toFixed(2).replace(".", ","),
    status: preview.course.status === "published" ? "Publicado" : "Rascunho",
    students: "Dados disponíveis no painel",
    image: fallbackCover,
    lessons: preview.lessons.map((lesson) => ({
      id: lesson.id,
      title: lesson.title,
      duration: `${lesson.duration_minutes} min`,
      videoName: "",
    })),
    materials: preview.materials.map((material) => ({
      id: material.id,
      title: material.title,
      kind: material.kind,
      fileName: material.external_url ?? material.title,
    })),
  };
}

export function CourseEditorIntegrated({ courseId }: { courseId?: string }) {
  const [initialCourse, setInitialCourse] = useState<TeacherCourse | null>(courseId ? null : blankTeacherCourse());
  const [originalLessonIds, setOriginalLessonIds] = useState<string[]>([]);
  const [originalMaterialIds, setOriginalMaterialIds] = useState<string[]>([]);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    if (!courseId) return;
    apiRequest<ApiCoursePreview>(`/api/courses/${courseId}/preview`, { headers: teacherHeaders() })
      .then((preview) => {
        setInitialCourse(previewToEditor(preview));
        setOriginalLessonIds(preview.lessons.map((lesson) => lesson.id));
        setOriginalMaterialIds(preview.materials.map((material) => material.id));
      })
      .catch(() => setLoadError("Não foi possível carregar este curso."));
  }, [courseId]);

  if (loadError) return <div className={styles.empty}><h1>Curso indisponível</h1><p>{loadError}</p><Link href="/professor/cursos">Voltar para meus cursos</Link></div>;
  if (!initialCourse) return <p>Carregando editor...</p>;

  return <CourseEditorForm initialCourse={initialCourse} originalLessonIds={originalLessonIds} originalMaterialIds={originalMaterialIds} isNew={!courseId} />;
}

function CourseEditorForm({ initialCourse, originalLessonIds, originalMaterialIds, isNew }: {
  initialCourse: TeacherCourse;
  originalLessonIds: string[];
  originalMaterialIds: string[];
  isNew: boolean;
}) {
  const router = useRouter();
  const [course, setCourse] = useState(initialCourse);
  const [preview, setPreview] = useState(false);
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  const [pendingMaterialFiles, setPendingMaterialFiles] = useState<Record<string, File>>({});

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

  function addMaterial(file: File) {
    const id = `material-${crypto.randomUUID()}`;
    const title = file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ");
    const extension = file.name.includes(".") ? file.name.split(".").pop()!.toUpperCase() : "Arquivo";
    setPendingMaterialFiles((current) => ({ ...current, [id]: file }));
    setCourse((current) => ({ ...current, materials: [...current.materials, { id, title, kind: extension, fileName: file.name, fileType: file.type, fileSize: file.size }] }));
  }

  function durationMinutes(value: string): number {
    const parsed = Number.parseInt(value.replace(/\D/g, ""), 10);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  async function synchronizeLessons(courseId: string): Promise<ApiLesson[]> {
    const currentIds = new Set(course.lessons.map((lesson) => lesson.id));
    await Promise.all(originalLessonIds.filter((id) => !currentIds.has(id)).map((id) => apiRequest<void>(`/api/courses/${courseId}/lessons/${id}`, { method: "DELETE", headers: teacherHeaders() })));
    const retainedIds = originalLessonIds.filter((id) => currentIds.has(id));
    await Promise.all(retainedIds.map((id, index) => apiRequest<ApiLesson>(`/api/courses/${courseId}/lessons/${id}`, {
      method: "PATCH",
      headers: teacherHeaders(),
      body: JSON.stringify({ position: 10_000 + index }),
    })));
    const saved: ApiLesson[] = [];
    for (const [position, lesson] of course.lessons.entries()) {
      const exists = originalLessonIds.includes(lesson.id);
      saved.push(await apiRequest<ApiLesson>(exists ? `/api/courses/${courseId}/lessons/${lesson.id}` : `/api/courses/${courseId}/lessons`, {
        method: exists ? "PATCH" : "POST",
        headers: teacherHeaders(),
        body: JSON.stringify({ title: lesson.title || `Aula ${position + 1}`, summary: "", duration_minutes: durationMinutes(lesson.duration), position, preview_available: false }),
      }));
    }
    return saved;
  }

  async function synchronizeMaterials(courseId: string): Promise<ApiMaterial[]> {
    const currentIds = new Set(course.materials.map((material) => material.id));
    await Promise.all(originalMaterialIds.filter((id) => !currentIds.has(id)).map((id) => apiRequest<void>(`/api/courses/${courseId}/materials/${id}`, { method: "DELETE", headers: teacherHeaders() })));
    const saved: ApiMaterial[] = [];
    for (const [position, material] of course.materials.entries()) {
      if (originalMaterialIds.includes(material.id)) {
        saved.push(await apiRequest<ApiMaterial>(`/api/courses/${courseId}/materials/${material.id}`, { method: "PATCH", headers: teacherHeaders(), body: JSON.stringify({ title: material.title, kind: material.kind, position }) }));
        continue;
      }
      const file = pendingMaterialFiles[material.id];
      if (!file) throw new Error(`Selecione novamente o arquivo do material “${material.title}”.`);
      const form = new FormData();
      form.append("file", file);
      form.append("title", material.title);
      form.append("kind", material.kind);
      form.append("access_level", "enrolled");
      form.append("position", String(position));
      saved.push(await apiRequest<ApiMaterial>(`/api/courses/${courseId}/materials/upload`, { method: "POST", headers: teacherHeaders(), body: form }));
    }
    return saved;
  }

  async function save(status: TeacherCourse["status"]) {
    if (!course.title.trim() || !course.subject.trim() || !course.summary.trim()) {
      setNotice("Preencha título, matéria e descrição antes de salvar.");
      return;
    }
    setSaving(true);
    setNotice("Salvando curso...");
    try {
      const payload = {
        title: course.title,
        subject: course.subject,
        area: "Geral",
        summary: course.summary,
        exams: course.exams.split(",").map((item) => item.trim()).filter(Boolean),
        access_type: course.access,
        price: course.access === "paid" ? Number(course.price.replace(",", ".")) : null,
      };
      const savedCourse = await apiRequest<ApiCourse>(isNew ? "/api/courses" : `/api/courses/${course.id}`, { method: isNew ? "POST" : "PATCH", headers: teacherHeaders(), body: JSON.stringify(payload) });
      await synchronizeLessons(savedCourse.id);
      await synchronizeMaterials(savedCourse.id);
      await apiRequest(`/api/courses/${savedCourse.id}/publication`, { method: "POST", headers: teacherHeaders(), body: JSON.stringify({ action: status === "Publicado" ? "publish" : "unpublish" }) });
      router.push("/professor/cursos?salvo=1");
      router.refresh();
    } catch (error) {
      setNotice(apiErrorMessage(error, error instanceof Error ? error.message : "Não foi possível salvar o curso."));
    } finally {
      setSaving(false);
    }
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
        <div className={styles.sectionHeading}><div><h2 id="lessons-title">2. Aulas</h2><p>Os dados das aulas serão salvos na API. O upload de vídeo será integrado separadamente.</p></div><button type="button" onClick={() => setCourse((current) => ({ ...current, lessons: [...current.lessons, { id: `aula-${crypto.randomUUID()}`, title: "", duration: "", videoName: "" }] }))}>+ Adicionar aula</button></div>
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
        <div className={styles.sectionHeading}><div><h2 id="materials-title">3. Materiais complementares</h2><p>Os arquivos serão enviados ao backend ao salvar.</p></div><DemoFileField accept=".pdf,.doc,.docx,.ppt,.pptx,.zip" inputLabel="Enviar material" onSelect={addMaterial} /></div>
        <div className={styles.rows}>{course.materials.length ? course.materials.map((material, index) => <div className={styles.materialRow} key={material.id}><label>Título<input aria-label={`Título do material ${index + 1}`} value={material.title} onChange={(event) => updateMaterial(index, "title", event.target.value)} /></label><label>Formato<select aria-label={`Formato do material ${index + 1}`} value={material.kind} onChange={(event) => updateMaterial(index, "kind", event.target.value)}><option>PDF</option><option>DOC</option><option>DOCX</option><option>PPT</option><option>PPTX</option><option>ZIP</option><option>Link</option></select></label><div className={styles.materialFile}><span>{material.fileName ?? material.title}</span><small>{material.fileType || material.kind}{material.fileSize ? ` · ${(material.fileSize / 1024).toFixed(0)} KB` : ""}</small></div><button type="button" onClick={() => setCourse((current) => ({ ...current, materials: current.materials.filter((_, position) => position !== index) }))}>Excluir</button></div>) : <p className={styles.emptyRow}>Nenhum material adicionado.</p>}</div>
      </section>

      {preview && <section className={styles.preview} aria-label="Prévia do curso"><span>Prévia</span><h2>{course.title || "Curso sem título"}</h2><p>{course.summary || "Adicione uma descrição para apresentar o curso."}</p><strong>{course.lessons.length} {course.lessons.length === 1 ? "aula" : "aulas"} · {course.access === "free" ? "Gratuito" : `R$ ${course.price}`}</strong></section>}
      {notice && <p className={styles.notice} role="status">{notice}</p>}
      <div className={styles.footerActions}><button className={styles.secondary} type="button" onClick={() => setPreview((current) => !current)}>{preview ? "Fechar prévia" : "Visualizar prévia"}</button><button className={styles.secondary} type="button" disabled={saving} onClick={() => save("Rascunho")}>Salvar rascunho</button><button className={styles.primary} type="button" disabled={saving} onClick={() => save("Publicado")}>Publicar curso</button></div>
    </div>
  );
}
