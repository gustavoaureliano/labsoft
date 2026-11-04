import { useEffect, useState } from "react";
import type { EnrolledLesson } from "@/data/courses";

export type Lesson = {
  id: string; course_id: string; title: string; description: string; position: number;
  media_id: string | null; thumbnail_id?: string | null; thumbnail_url?: string;
  duration_seconds?: number | null; playable?: boolean; position_seconds?: number; completed?: boolean;
};
export type Playback = Lesson & { content_url: string; media_id: string; position_seconds: number; completed: boolean };
export type Course = {
  id: string; title: string; owner_id: string; image: string; teacher: string;
  access_status: "active" | "expired" | "blocked";
  lessons: Lesson[]; sections: {title: string; lesson_ids: string[]}[];
  progress: number; completed: boolean; total_lessons: number; completed_lessons: number; continue_lesson: Lesson | null;
};
export type Dashboard = { courses: Course[]; current_course: Course | null; recommendations: Course[]; notifications: {title?: string; message?: string}[] };

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, { ...options, cache: "no-store" });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : `Falha na API (${response.status})`);
  }
  return response.status === 204 ? undefined as T : response.json();
}

export function jsonRequest(method: string, data: unknown): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) };
}

export function useApi<T>(path: string | null) {
  const [result, setResult] = useState<{path: string; data?: T; error?: string} | null>(null);
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    api<T>(path, { signal: controller.signal }).then(
      data => setResult({path, data}),
      error => { if (!controller.signal.aborted) setResult({path, error: error.message}); },
    );
    return () => controller.abort();
  }, [path]);
  return { data: result?.path === path ? result.data : undefined, error: result?.path === path ? result.error : undefined };
}

export function lessonLink(id: string, context?: {origin?: string; playlistId?: string}) {
  const query = new URLSearchParams({aula: id});
  if (context?.origin) query.set("origem", context.origin);
  if (context?.playlistId) query.set("lista", context.playlistId);
  return `/videoaula?${query}`;
}

export function displayLessons(lessons: Lesson[], activeId?: string): EnrolledLesson[] {
  return lessons.map(lesson => ({
    id: lesson.id, number: String(lesson.position).padStart(2, "0"), title: lesson.title,
    description: lesson.description, thumbnail: lesson.thumbnail_url,
    duration: lesson.duration_seconds ? `${Math.ceil(lesson.duration_seconds / 60)} min` : "Em preparação",
    status: lesson.playable === false ? "Indisponível" : lesson.completed ? "Concluída" : lesson.id === activeId ? "Aula atual" : "Próxima aula",
  }));
}
