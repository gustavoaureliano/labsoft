import { notFound } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { CourseLessonList } from "@/components/learning/CourseLessonList";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { currentLesson, enrolledCourse, lessonHref, questionHref } from "@/data/courses";
import styles from "./page.module.css";

export default async function StudentCoursePage({ params }: PageProps<"/meus-cursos/[id]">) {
  if ((await params).id !== enrolledCourse.id) notFound();

  return (
    <AppShell activePage="courses">
      <div className={styles.page}>
        <Link className={styles.back} href="/meus-cursos">← Voltar para Meus Cursos</Link>
        <header className={styles.hero}>
          <div><span className={styles.eyebrow}>{enrolledCourse.category} · {enrolledCourse.totalLessons} aulas</span><h1>{enrolledCourse.title}</h1><p>{enrolledCourse.summary}</p><small>{enrolledCourse.teacher}</small></div>
          <aside><div><span>Progresso do curso</span><strong>{enrolledCourse.progress}%</strong></div><ProgressBar value={enrolledCourse.progress} /><Link href={lessonHref(currentLesson.id)}>Continuar na aula {currentLesson.number}</Link><Link className={styles.secondaryAction} href={questionHref()}>Tirar dúvida sobre este curso</Link></aside>
        </header>
        <section className={styles.content} aria-labelledby="course-content-title">
          <div className={styles.heading}><span className={styles.eyebrow}>Sua trilha</span><h2 id="course-content-title">Conteúdo do curso</h2><p>Escolha uma aula para assistir ou revisar.</p></div>
          {enrolledCourse.modules.map((module) => <section className={styles.module} key={module.title}><h3>{module.title}</h3><CourseLessonList lessons={enrolledCourse.lessons.filter((lesson) => module.lessonIds.includes(lesson.id))} activeLessonId={currentLesson.id} /></section>)}
        </section>
      </div>
    </AppShell>
  );
}
