"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { CatalogCourseCard } from "@/components/catalog/CatalogCourseCard";
import { courseGroups, type CatalogCourse } from "@/data/catalog";
import { toCatalogCourse } from "@/lib/api/adapters";
import { apiRequest } from "@/lib/api/client";
import type { ApiCoursePage, ApiSearch } from "@/lib/api/types";
import styles from "./page.module.css";

export default function ExplorarCursos() {
  const [query, setQuery] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("Todos");
  const [sortOrder, setSortOrder] = useState("relevance");
  const [courses, setCourses] = useState<CatalogCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        const term = query.trim();
        if (term.length >= 2) {
          const response = await apiRequest<ApiSearch>(`/api/search?q=${encodeURIComponent(term)}&limit=100`);
          let items = response.courses.map((course) => toCatalogCourse(course));
          if (selectedGroup !== "Todos") items = items.filter((course) => course.group === selectedGroup);
          if (sortOrder === "rating") items.sort((a, b) => b.rating - a.rating);
          if (sortOrder === "title") items.sort((a, b) => a.title.localeCompare(b.title, "pt-BR"));
          setCourses(items);
        } else {
          const params = new URLSearchParams({ order: sortOrder, page: "1", size: "100" });
          if (selectedGroup !== "Todos") params.set("area", selectedGroup);
          const response = await apiRequest<ApiCoursePage>(`/api/courses?${params}`);
          setCourses(response.items.map((course) => toCatalogCourse(course)));
        }
        setError("");
      } catch {
        setCourses([]);
        setError("Não foi possível carregar o catálogo.");
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [query, selectedGroup, sortOrder]);

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
            <span aria-live="polite">{courses.length} {courses.length === 1 ? "curso encontrado" : "cursos encontrados"}</span>
          </div>
          {loading ? <p className={styles.emptyState}>Carregando cursos...</p> : error ? <p className={styles.emptyState}>{error}</p> : courses.length ? (
            <div className={styles.courseGrid}>
              {courses.map((course) => <CatalogCourseCard course={course} key={course.id} />)}
            </div>
          ) : (
            <p className={styles.emptyState}>Nenhum curso encontrado. Tente outra busca ou matéria.</p>
          )}
        </section>
      </div>
    </AppShell>
  );
}
