"use client";

import { useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { catalogCourses, complementaryMaterials, materialTypes } from "@/data/catalog";
import styles from "./page.module.css";

export default function MateriaisComplementares() {
  const [selectedCourse, setSelectedCourse] = useState("Todos");
  const [selectedType, setSelectedType] = useState("Todos");
  const filteredMaterials = complementaryMaterials.filter((material) =>
    (selectedCourse === "Todos" || material.courseId === selectedCourse)
    && (selectedType === "Todos" || material.type === selectedType),
  );
  const groupedMaterials = filteredMaterials.reduce<Record<string, typeof filteredMaterials>>((groups, material) => {
    groups[material.courseTitle] ??= [];
    groups[material.courseTitle].push(material);
    return groups;
  }, {});
  const courseOptions = catalogCourses.filter((course) => complementaryMaterials.some((material) => material.courseId === course.id));

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
            <select value={selectedCourse} onChange={(event) => setSelectedCourse(event.target.value)}>
              <option value="Todos">Todos os cursos</option>
              {courseOptions.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}
            </select>
          </label>
          <label>
            <span>Tipo de material</span>
            <select value={selectedType} onChange={(event) => setSelectedType(event.target.value)}>
              <option value="Todos">Todos os tipos</option>
              {materialTypes.map((type) => <option key={type} value={type}>{type}</option>)}
            </select>
          </label>
          <span className={styles.resultCount} aria-live="polite">{filteredMaterials.length} materiais</span>
        </section>

        {filteredMaterials.length ? (
          <div className={styles.groups}>
            {Object.entries(groupedMaterials).map(([courseTitle, materials]) => (
              <section aria-labelledby={`course-${materials[0].courseId}`} className={styles.courseGroup} key={courseTitle}>
                <div className={styles.groupHeading}>
                  <div>
                    <span>Material do curso</span>
                    <h2 id={`course-${materials[0].courseId}`}>{courseTitle}</h2>
                  </div>
                  <Link href={`/pesquisa?q=${encodeURIComponent(courseTitle)}`}>Ver curso</Link>
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
                      <span className={styles.format}>{material.format}</span>
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