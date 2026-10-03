import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { CatalogCourseCard } from "@/components/catalog/CatalogCourseCard";
import { HomeDashboard } from "@/components/home/HomeDashboard";
import { AppShell } from "@/components/layout/AppShell";
import { catalogCourses } from "@/data/catalog";
import { demoRoleCookieName, parseDemoRole, roleHome } from "@/data/demoAccount";
import styles from "./page.module.css";

export default async function HomePage() {
  const role = parseDemoRole((await cookies()).get(demoRoleCookieName)?.value);

  if (role === "student") return <AppShell><HomeDashboard /></AppShell>;
  if (role) redirect(roleHome[role]);

  return <LandingPage />;
}

function LandingPage() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.brand}><Logo /></div>
        <nav className={styles.accountLinks} aria-label="Acesso à conta">
          <Link href="/login">Entrar</Link>
          <Link className={styles.primaryLink} href="/cadastro">Criar conta</Link>
        </nav>
      </header>

      <main>
        <section className={styles.hero} aria-labelledby="hero-title">
          <div className={styles.heroContent}>
            <span className={styles.eyebrow}>Seu próximo passo começa aqui</span>
            <h1 id="hero-title">Estude com foco no vestibular e chegue mais longe.</h1>
            <p>Encontre cursos, acompanhe suas aulas e organize seus estudos em um só lugar.</p>
            <div className={styles.heroActions}>
              <Link className={styles.primaryLink} href="/cadastro">Começar agora</Link>
              <Link className={styles.secondaryLink} href="/login">Já tenho conta</Link>
            </div>
          </div>
          <div className={styles.heroHighlight} aria-hidden="true">
            <span>Aprenda no seu ritmo</span>
            <strong>Um lugar para continuar aprendendo, aula após aula.</strong>
          </div>
        </section>

        <section className={styles.courses} aria-labelledby="courses-title">
          <div className={styles.sectionHeading}>
            <span className={styles.eyebrow}>Conheça a plataforma</span>
            <h2 id="courses-title">Cursos para começar sua jornada</h2>
            <p>Uma amostra dos conteúdos disponíveis para quem entra na AprovaAí.</p>
          </div>
          <div className={styles.courseGrid}>
            {catalogCourses.slice(0, 3).map((course) => <CatalogCourseCard course={course} key={course.id} />)}
          </div>
          <Link className={styles.exploreLink} href="/login">Entre para explorar todos os cursos →</Link>
        </section>
      </main>

      <footer className={styles.footer}>AprovaAí · Protótipo de uma plataforma de estudos</footer>
    </div>
  );
}
