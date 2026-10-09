"use client";

import { useState, type FormEvent } from "react";
import Image from "next/image";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { CatalogCourseCard } from "@/components/catalog/CatalogCourseCard";
import { CourseLessonList } from "@/components/learning/CourseLessonList";
import { PrimaryLink } from "@/components/ui/PrimaryLink";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { currentLesson, enrolledCourse, lessonHref, lessonsFromIds } from "@/data/courses";
import { catalogCourses } from "@/data/catalog";
import { accessDemoKey, initialAccessDemo } from "@/data/subscriptionDemo";
import { initialStudyDemo, studyDemoKey } from "@/data/studyDemo";
import { useDemoStorage } from "@/lib/useDemoStorage";
import styles from "./page.module.css";

export default function MeusCursos() {
  const [activeTab, setActiveTab] = useState<"history" | "favorites" | "playlists">("history");
  const [study, saveStudy] = useDemoStorage(studyDemoKey, initialStudyDemo);
  const [access] = useDemoStorage(accessDemoKey, initialAccessDemo);
  const [playlistName, setPlaylistName] = useState("");
  const acquiredCourses = catalogCourses.filter((course) => access.courseIds.includes(course.id));
  const historyLessons = lessonsFromIds(study.viewedLessons);
  const favoriteLessons = lessonsFromIds(study.favoriteLessons);

  function createPlaylist(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = playlistName.trim();
    if (!name || study.playlists.some((playlist) => playlist.name.toLocaleLowerCase("pt-BR") === name.toLocaleLowerCase("pt-BR"))) return;
    saveStudy({ ...study, playlists: [...study.playlists, { id: crypto.randomUUID(), name, lessonIds: [] }] });
    setPlaylistName("");
  }

  return (
    <AppShell activePage="courses">
      <div className={styles.page}>
        <header className={styles.heading}>
          <span className={styles.eyebrow}>Sua jornada de aprendizado</span>
          <h1>Meus cursos</h1>
          <p>Acompanhe seu progresso e continue de onde parou.</p>
        </header>

        <section aria-labelledby="in-progress-title">
          <h2 id="in-progress-title">Em andamento</h2>
          <article className={styles.course}>
            <div className={styles.courseVisual}><Image alt={`Capa do curso ${enrolledCourse.title}`} fill priority sizes="(max-width: 750px) 100vw, 40vw" src={enrolledCourse.image} /><span>{enrolledCourse.category}</span></div>
            <div className={styles.courseContent}>
              <span className={styles.eyebrow}>{enrolledCourse.category} · {enrolledCourse.totalLessons} aulas</span>
              <h3><Link href={`/meus-cursos/${enrolledCourse.id}`}>{enrolledCourse.title}</Link></h3>
              <p>{enrolledCourse.teacher}</p>
              <div className={styles.progressCopy}><span>Progresso do curso</span><strong>{enrolledCourse.progress}%</strong></div>
              <ProgressBar value={enrolledCourse.progress} />
              <p className={styles.nextLesson}>Próxima aula: {currentLesson.title}</p>
              <div className={styles.courseActions}><PrimaryLink className={styles.primaryButton} href={lessonHref(currentLesson.id)}>Continuar curso</PrimaryLink><Link href={`/meus-cursos/${enrolledCourse.id}`}>Ver todas as aulas</Link></div>
            </div>
          </article>
        </section>

        {(acquiredCourses.length > 0 || access.subscription?.plan === "complete") && <section aria-labelledby="new-access-title">
          <h2 id="new-access-title">Acessos adicionados</h2>
          {access.subscription?.plan === "complete" && access.subscription.status === "active" && <p className={styles.accessNotice}>Sua assinatura completa está ativa nesta demonstração.</p>}
          {acquiredCourses.length > 0 && <div className={styles.acquiredGrid}>{acquiredCourses.map((course) => <CatalogCourseCard course={course} key={course.id} />)}</div>}
        </section>}

        <section className={styles.library} aria-labelledby="library-title">
          <h2 id="library-title">Sua biblioteca de estudo</h2>
          <div className={styles.tabs} aria-label="Organizar estudos">
            <button type="button" aria-pressed={activeTab === "history"} onClick={() => setActiveTab("history")}>Histórico</button>
            <button type="button" aria-pressed={activeTab === "favorites"} onClick={() => setActiveTab("favorites")}>Favoritos</button>
            <button type="button" aria-pressed={activeTab === "playlists"} onClick={() => setActiveTab("playlists")}>Playlists</button>
          </div>
          <div className={styles.libraryContent}>
            {activeTab === "history" && (historyLessons.length > 0 ? <CourseLessonList lessons={historyLessons} getLessonHref={(lesson) => lessonHref(lesson.id, { origin: "history" })} /> : <p>Abra uma videoaula para começar seu histórico neste navegador.</p>)}
            {activeTab === "favorites" && (favoriteLessons.length > 0 ? <CourseLessonList lessons={favoriteLessons} getLessonHref={(lesson) => lessonHref(lesson.id, { origin: "favorites" })} /> : <p>Você ainda não salvou uma aula nos favoritos.</p>)}
            {activeTab === "playlists" && <>
              <form className={styles.playlistForm} onSubmit={createPlaylist}><label htmlFor="playlist-name">Nova playlist</label><input id="playlist-name" value={playlistName} onChange={(event) => setPlaylistName(event.target.value)} maxLength={60} placeholder="Ex.: Revisão de Física" /><button type="submit" disabled={!playlistName.trim()}>Criar playlist</button></form>
              <ul className={styles.playlistList}>{study.playlists.map((playlist) => <li key={playlist.id}><Link href={`/meus-cursos/playlists/${playlist.id}`}><span><strong>{playlist.name}</strong><small>{playlist.lessonIds.length} {playlist.lessonIds.length === 1 ? "aula" : "aulas"}</small></span><b>Ver playlist →</b></Link></li>)}</ul>
            </>}
          </div>
          <p className={styles.demoNote}>Histórico, favoritos e playlists ficam somente neste navegador.</p>
        </section>
      </div>
    </AppShell>
  );
}
