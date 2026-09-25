import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { CatalogCourseCard } from "@/components/catalog/CatalogCourseCard";
import { searchCatalogCourses, searchCatalogMaterials } from "@/data/catalog";
import styles from "./page.module.css";

type SearchPageProps = {
  searchParams: Promise<{ q?: string | string[] }>;
};

export default async function Pesquisa({ searchParams }: SearchPageProps) {
  const params = await searchParams;
  const query = Array.isArray(params.q) ? params.q[0] ?? "" : params.q ?? "";
  const courses = searchCatalogCourses(query);
  const materials = searchCatalogMaterials(query);
  const hasQuery = query.trim().length > 0;

  return (
    <AppShell activePage="explore">
      <div className={styles.page}>
        <header className={styles.heading}>
          <span>Busca na biblioteca</span>
          <h1>Resultados da pesquisa</h1>
          {hasQuery ? <p>Para “{query}”</p> : <p>Digite um termo para buscar cursos e materiais.</p>}
        </header>

        {hasQuery && (courses.length > 0 || materials.length > 0) ? (
          <>
            {courses.length > 0 && (
              <section aria-labelledby="course-results-title">
                <div className={styles.sectionHeading}>
                  <h2 id="course-results-title">Cursos</h2>
                  <span>{courses.length} encontrados</span>
                </div>
                <div className={styles.courseGrid}>
                  {courses.map((course) => <CatalogCourseCard course={course} key={course.id} />)}
                </div>
              </section>
            )}

            {materials.length > 0 && (
              <section aria-labelledby="material-results-title">
                <div className={styles.sectionHeading}>
                  <h2 id="material-results-title">Materiais complementares</h2>
                  <span>{materials.length} encontrados</span>
                </div>
                <ul className={styles.materialList}>
                  {materials.map((material) => (
                    <li className={styles.material} key={material.id}>
                      <div className={styles.materialType}>{material.type}</div>
                      <div className={styles.materialCopy}>
                        <h3>{material.title}</h3>
                        <p>{material.description}</p>
                        <span>{material.courseTitle} · {material.format}</span>
                      </div>
                      <Link href="/materiais-complementares">Ver biblioteca</Link>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        ) : (
          <div className={styles.emptyState}>
            <h2>{hasQuery ? "Nenhum resultado encontrado" : "Comece uma nova busca"}</h2>
            <p>{hasQuery ? "Tente outro termo, matéria, professor ou tipo de material." : "Pesquise por matéria, curso, professor ou material."}</p>
            <form action="/pesquisa" role="search">
              <label>
                <span className={styles.visuallyHidden}>Buscar na biblioteca</span>
                <input name="q" placeholder="Ex.: biologia, redação, exercícios" type="search" />
              </label>
              <button type="submit">Buscar</button>
            </form>
            <Link className={styles.exploreLink} href="/explorar-cursos">Explorar cursos</Link>
          </div>
        )}
      </div>
    </AppShell>
  );
}