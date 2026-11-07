"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import type { ComplementaryMaterial } from "@/data/catalog";
import { toComplementaryMaterial } from "@/lib/api/adapters";
import { absoluteApiUrl, apiRequest, studentHeaders } from "@/lib/api/client";
import { isApiConfigured } from "@/lib/apiClient";
import type { Course as LearningCourse } from "@/lib/api/learning";
import type { ApiCoursePage, ApiMaterialList } from "@/lib/api/types";
import styles from "./page.module.css";

type LibraryMaterial = ComplementaryMaterial & {
  authorized: boolean;
  downloadUrl: string | null;
  externalRestricted: boolean;
};

export default function MateriaisComplementares({searchParams}: PageProps<"/materiais-complementares">) {
  const {curso, aula} = use(searchParams);
  const initialCourse = typeof curso === "string" ? curso : "Todos";
  const lessonId = typeof aula === "string" ? aula : null;
  return <MaterialsLibrary key={`${initialCourse}:${lessonId ?? ""}`} initialCourse={initialCourse} lessonId={lessonId} />;
}

function MaterialsLibrary({initialCourse, lessonId}: {initialCourse: string; lessonId: string | null}) {
  const [selectedCourse, setSelectedCourse] = useState(initialCourse);
  const [selectedType, setSelectedType] = useState("Todos");
  const [materials, setMaterials] = useState<LibraryMaterial[]>([]);
  const [courseOptions, setCourseOptions] = useState<Array<{ id: string; title: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const materialTypes = [...new Set(materials.map((material) => material.type))];
  const filteredMaterials = materials.filter((material) =>
    (selectedCourse === "Todos" || material.courseId === selectedCourse)
    && (selectedType === "Todos" || material.type === selectedType),
  );
  const groupedMaterials = filteredMaterials.reduce<Record<string, typeof filteredMaterials>>((groups, material) => {
    groups[material.courseTitle] ??= [];
    groups[material.courseTitle].push(material);
    return groups;
  }, {});

  useEffect(() => {
    async function loadMaterials() {
      try {
        const courses = isApiConfigured
          ? await apiRequest<LearningCourse[]>("/api/learning/courses")
          : (await apiRequest<ApiCoursePage>("/api/courses?page=1&size=100")).items;
        const lists = await Promise.all(courses.map(async (course) => {
          const lesson = lessonId && course.id === initialCourse ? `?lesson_id=${encodeURIComponent(lessonId)}` : "";
          const list = await apiRequest<ApiMaterialList>(`/api/courses/${course.id}/materials${lesson}`, { headers: studentHeaders() });
          return list.items.map((material) => ({
            ...toComplementaryMaterial(material, course.title),
            authorized: material.authorized,
            downloadUrl: material.download_url,
            externalRestricted: material.access_level === "enrolled" && Boolean(material.external_url),
          }));
        }));
        setCourseOptions(courses.map((course) => ({ id: course.id, title: course.title })));
        setMaterials(lists.flat());
        setError("");
      } catch {
        setError("Não foi possível carregar os materiais.");
      } finally {
        setLoading(false);
      }
    }
    loadMaterials();
  }, [initialCourse, lessonId]);

  return (
    <AppShell activePage="materials">
      <div className={styles.page}>
        <header className={styles.heading}>
          <span>Continue aprendendo</span>
          <h1>Materiais complementares</h1>
          <p>Resumos, exercícios e revisões para acompanhar seus cursos.</p>
        </header>

        <section className={styles.library} aria-label="Filtros de materiais">
          <label>
            <span>Curso</span>
            <select name="course-filter" value={selectedCourse} onChange={(event) => setSelectedCourse(event.target.value)}>
              <option value="Todos">Todos os cursos</option>
              {courseOptions.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}
            </select>
          </label>
          <label>
            <span>Tipo de material</span>
            <select name="type-filter" value={selectedType} onChange={(event) => setSelectedType(event.target.value)}>
              <option value="Todos">Todos os tipos</option>
              {materialTypes.map((type) => <option key={type} value={type}>{type}</option>)}
            </select>
          </label>
          <span className={styles.resultCount} aria-live="polite">{filteredMaterials.length} {filteredMaterials.length === 1 ? "material" : "materiais"}</span>
        </section>

        {loading ? <p className={styles.emptyState}>Carregando materiais...</p> : error ? <p className={styles.emptyState}>{error}</p> : filteredMaterials.length ? (
          <div className={styles.groups}>
            {Object.entries(groupedMaterials).map(([courseTitle, materials]) => (
              <section aria-labelledby={`course-${materials[0].courseId}`} className={styles.courseGroup} key={courseTitle}>
                <div className={styles.groupHeading}>
                  <div>
                    <span>Material do curso</span>
                    <h2 id={`course-${materials[0].courseId}`}>{courseTitle}</h2>
                  </div>
                  <Link href={`/pesquisa?q=${encodeURIComponent(courseTitle)}`}>Buscar curso</Link>
                </div>
                <ul className={styles.materialList}>
                  {materials.map((material) => (
                    <li className={styles.material} key={material.id}>
                      <div className={styles.typeMark} aria-hidden="true">{material.type.slice(0, 1)}</div>
                      <div className={styles.materialCopy}>
                        <span>{material.type}</span>
                        <h3>{material.title}</h3>
                        <p>{material.description}</p>
                      </div>
                      {material.downloadUrl && material.authorized
                        ? <a className={styles.format} href={absoluteApiUrl(material.downloadUrl)} rel="noreferrer" target="_blank">Abrir {material.format}</a>
                        : <span className={styles.format}>{material.authorized ? material.format : "Matrícula necessária"}</span>}
                      {material.authorized && material.externalRestricted && <p>Link externo: depois de aberto, o acesso ao destino não pode ser revogado pela plataforma.</p>}
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        ) : (
          <p className={styles.emptyState}>Nenhum material corresponde a esses filtros.</p>
        )}
      </div>
    </AppShell>
  );
}
