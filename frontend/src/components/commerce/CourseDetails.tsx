"use client";

import Link from "next/link";
import type { CatalogCourse } from "@/data/catalog";
import { formatPrice } from "@/data/catalog";
import { accessDemoKey, initialAccessDemo } from "@/data/subscriptionDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { useApi, type Course } from "@/lib/api/learning";
import styles from "./Commerce.module.css";

export function CourseDetails({ course }: { course: CatalogCourse }) {
  const [access, , ready] = useDemoStorage(accessDemoKey, initialAccessDemo);
  const learning = useApi<Course[]>("/api/learning/courses");
  const accessibleCourse = learning.data?.find(item => item.id === course.id);
  const hasDemoAccess = access.courseIds.includes(course.id) || (access.subscription?.status === "active" && access.subscription.plan === "complete");

  let accessLabel = course.access === "free" ? "Acesso gratuito" : "Acesso ao curso";
  let accessValue = course.access === "free" ? "Gratuito" : formatPrice(course.price);
  let accessDescription = course.access === "free" ? "Adicione este curso à sua área de estudos." : "Compre somente este curso ou escolha a assinatura completa.";
  let action: { href: string; label: string } | null = { href: course.access === "free" ? `/checkout?curso=${course.id}&tipo=curso` : `/planos?curso=${course.id}`, label: course.access === "free" ? "Adicionar aos meus cursos" : "Escolher acesso" };

  if (accessibleCourse?.access_status === "active") {
    accessLabel = accessibleCourse.completed ? "Curso concluído" : "Curso disponível";
    accessValue = `${accessibleCourse.progress}% concluído`;
    accessDescription = "Seu acesso está disponível na área de estudos.";
    action = { href: `/meus-cursos/${course.id}`, label: "Continuar curso" };
  } else if (accessibleCourse?.access_status === "expired" || accessibleCourse?.access_status === "blocked") {
    accessLabel = accessibleCourse.access_status === "expired" ? "Acesso expirado" : "Acesso bloqueado";
    accessValue = "Aula indisponível";
    accessDescription = "Entre em contato com o suporte para verificar sua situação de acesso.";
    action = null;
  } else if (!learning.data && !learning.error) {
    accessLabel = "Verificando acesso";
    accessValue = "Aguarde";
    accessDescription = "Consultando seus cursos na API.";
    action = null;
  } else if (learning.error) {
    accessLabel = "Acesso indisponível";
    accessValue = "Tente novamente";
    accessDescription = learning.error;
    action = null;
  } else if (!ready) {
    accessLabel = "Verificando acesso";
    accessValue = "Aguarde";
    accessDescription = "Consultando os acessos salvos neste navegador.";
    action = null;
  } else if (hasDemoAccess) {
    accessLabel = "Curso adquirido";
    accessValue = "Acesso confirmado";
    accessDescription = "A compra demonstrativa já foi concluída neste navegador.";
    action = { href: "/meus-cursos", label: "Voltar para Meus Cursos" };
  }

  return (
    <div className={styles.page}>
      <Link className={styles.back} href="/explorar-cursos">← Voltar para cursos</Link>
      <section className={styles.hero}>
        <div className={styles.heroMain}>
          <span className={styles.eyebrow}>{course.subject} · {course.exams.join(" e ")}</span>
          <h1>{course.title}</h1>
          <p className={styles.lead}>{course.summary}</p>
          <div className={styles.meta}><span>{course.lessonCount} aulas</span><span>{course.duration}</span><span>★ {course.rating.toFixed(1).replace(".", ",")}</span></div>
        </div>
        <aside className={styles.purchase} aria-label="Opções de acesso">
          <span className={styles.eyebrow}>{accessLabel}</span>
          <strong>{accessValue}</strong>
          <p>{accessDescription}</p>
          {action && <Link className={styles.primary} href={action.href}>{action.label}</Link>}
        </aside>
      </section>

      <div className={styles.detailsGrid}>
        <section className={styles.section} aria-labelledby="syllabus-title">
          <h2 id="syllabus-title">Ementa do curso</h2>
          <div className={styles.modules}>{course.syllabus.map((module) => <div className={styles.module} key={module.title}><h3>{module.title}</h3><ul>{module.lessons.map((lesson) => <li key={lesson}>{lesson}</li>)}</ul></div>)}</div>
        </section>
        <div className={styles.page}>
          <section className={styles.section}><h2>Para quem é</h2><p>{course.audience}</p></section>
          <section className={styles.section}><h2>Professor</h2><p><strong>{course.teacher}</strong></p><p>Conteúdo organizado para uma preparação objetiva e progressiva.</p></section>
        </div>
      </div>
    </div>
  );
}
