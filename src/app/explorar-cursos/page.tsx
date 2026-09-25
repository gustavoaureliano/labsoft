"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { CatalogCourseCard } from "@/components/catalog/CatalogCourseCard";
import { catalogCourses, courseGroups } from "@/data/catalog";
import styles from "./page.module.css";

export default function ExplorarCursos() {
  const [query, setQuery] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("Todos");
  const [sortOrder, setSortOrder] = useState("relevance");
  const normalizedQuery = query.trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
  const filteredCourses = catalogCourses
    .filter((course) => selectedGroup === "Todos" || course.group === selectedGroup)
    .filter((course) => !normalizedQuery || [course.title, course.subject, course.group, course.teacher, course.summary, ...course.exams]
      .join(" ").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR").includes(normalizedQuery))
    .sort((first, second) => {
      if (sortOrder === "rating") return second.rating - first.rating;
      if (sortOrder === "title") return first.title.localeCompare(second.title, "pt-BR");
      return 0;
    });

  return (
    <AppShell activePage="explore">
      <div className={styles.page}>
        <header className={styles.heading}>
          <h1>Explore cursos</h1>
          <p>Encontre o curso ideal para o seu vestibular</p>
          <span>Conteúdos por matéria, professor e exame.</span>
        </header>

        <div className={styles.controls}>
          <label className={styles.searchField}>
            <span>Buscar cursos, temas ou professores</span>
            <input
              name="course-query"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ex.: biologia celular"
            />
          </label>
          <label className={styles.sortField}>
            <span>Ordenar por</span>
            <select name="sort" value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
              <option value="relevance">Mais relevantes</option>
              <option value="rating">Melhor avaliados</option>
              <option value="title">Ordem alfabética</option>
            </select>
          </label>
        </div>

        <div className={styles.filters} aria-label="Filtrar por matéria">
          {["Todos", ...courseGroups].map((group) => (
            <button
              aria-pressed={selectedGroup === group}
              className={selectedGroup === group ? styles.filterActive : ""}
              key={group}
              onClick={() => setSelectedGroup(group)}
              type="button"
            >
              {group}
            </button>
          ))}
        </div>

        <section aria-labelledby="courses-title">
          <div className={styles.resultsHeading}>
            <h2 id="courses-title">Cursos em destaque</h2>
            <span aria-live="polite">{filteredCourses.length} {filteredCourses.length === 1 ? "curso encontrado" : "cursos encontrados"}</span>
          </div>
          {filteredCourses.length ? (
            <div className={styles.courseGrid}>
              {filteredCourses.map((course) => <CatalogCourseCard course={course} key={course.id} />)}
            </div>
          ) : (
            <p className={styles.emptyState}>Nenhum curso encontrado. Tente outra busca ou matéria.</p>
          )}
        </section>
      </div>
    </AppShell>
  );
}
