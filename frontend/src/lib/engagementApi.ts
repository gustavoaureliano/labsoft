"use client";

import { useCallback, useEffect, useState } from "react";
import { demoAccountKey, demoRoleCookieName, type DemoAccount, type DemoRole } from "@/data/demoAccount";
import { initialStudyDemo, type StudyDemo } from "@/data/studyDemo";

export type ApiPlaylist = {
  id: string;
  name: string;
  lesson_ids: string[];
};

export type ApiComment = {
  id: string;
  lesson_id: string;
  author_id: string;
  author_name: string;
  parent_id: string | null;
  content: string;
  moderation_status: string;
  created_at: string;
};

export type ApiRatingSummary = {
  target_type: "lesson" | "course";
  target_id: string;
  student_stars: number | null;
  average_rating: number;
  total_ratings: number;
};

export type ApiQuestion = {
  id: string;
  student_id: string;
  student_name: string;
  course_id: string;
  course_title: string;
  lesson_id: string | null;
  lesson_title: string;
  teacher_id: string;
  teacher_name: string;
  prompt: string;
  status: "pending" | "answered";
  answer: string | null;
  created_at: string;
  answered_at: string | null;
};

export type ApiNotification = {
  id: string;
  user_id: string;
  kind: string;
  title: string;
  description: string;
  destination_url: string;
  is_read: boolean;
  created_at: string;
};

export type ApiModerationQueueItem = {
  queue_id: string;
  item_type: "lesson" | "course" | "comment";
  item_id: string;
  title_or_excerpt: string;
  author_or_owner: string;
  reasons: string[];
  reports_count: number;
  status: "pending" | "kept" | "hidden" | "deleted";
  created_at: string;
};

export type ApiMyReportStatus = {
  reported: boolean;
  reason: string | null;
  status: "pending" | "resolved" | null;
  decision: "mantido" | "ocultado" | "excluído" | null;
};

export type ApiTeacherAnalytics = {
  teacher_id: string;
  period: "30d" | "90d" | "365d";
  course_id: string | null;
  enrollments: { value: number; source: string; description: string };
  active_students: { value: number; source: string; description: string };
  completion_rate: { value: number; source: string; description: string };
  average_rating: { value: number; source: string; description: string };
  total_ratings: { value: number; source: string; description: string };
  question_response_rate: { value: number; source: string; description: string };
  courses: {
    course_id: string;
    course_title: string;
    enrollments: number;
    active_students: number;
    completion_rate: number;
    avg_watch_minutes: number;
    average_rating: number;
    total_ratings: number;
    pending_questions: number;
    answered_questions: number;
  }[];
};

export type ApiAdminDashboard = {
  period: "monthly" | "annual";
  total_users: number;
  total_students: number;
  total_teachers: number;
  total_courses: number;
  total_accesses_in_period: number;
  pending_moderation_items: number;
  held_comments_count: number;
  access_series: { label: string; count: number }[];
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const roleToUser: Record<DemoRole, string> = {
  student: "aluno-demo",
  teacher: "professor-demo",
  admin: "admin-demo",
};

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const cookies = document.cookie ? document.cookie.split("; ") : [];
  for (const part of cookies) {
    const eqIndex = part.indexOf("=");
    if (eqIndex === -1) continue;
    const key = part.slice(0, eqIndex).trim();
    if (key === name) {
      return decodeURIComponent(part.slice(eqIndex + 1));
    }
  }
  return null;
}

export function resolveDemoUserHeader(): string | null {
  const directUser = readCookie("aprovaai_demo_user");
  if (directUser) return directUser;

  const roleCookie = readCookie(demoRoleCookieName) as DemoRole | null;
  if (roleCookie && roleToUser[roleCookie]) {
    return roleToUser[roleCookie];
  }

  if (typeof window !== "undefined") {
    try {
      const raw = window.localStorage.getItem(demoAccountKey);
      if (raw) {
        const account = JSON.parse(raw) as DemoAccount;
        if (account?.role && roleToUser[account.role]) {
          return roleToUser[account.role];
        }
      }
    } catch {
      // Ignore storage access errors
    }
  }
  return null;
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const headers = new Headers(init.headers);
  const demoUser = resolveDemoUserHeader();
  if (demoUser && !headers.has("X-Demo-User")) {
    headers.set("X-Demo-User", demoUser);
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(path, {
    ...init,
    headers,
    credentials: "same-origin",
  });

  if (!res.ok) {
    let detail = `Erro na requisição (${res.status})`;
    try {
      const errBody = (await res.json()) as { detail?: string };
      if (typeof errBody?.detail === "string") {
        detail = errBody.detail;
      }
    } catch {
      // Ignore non-JSON error body
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

const LIBRARY_SYNC_EVENT = "aprovaai-library-sync";

export function useStudyLibrary() {
  const [study, setStudy] = useState<StudyDemo>({
    viewedLessons: [],
    favoriteLessons: [],
    playlists: [],
  });
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshFromBackend = useCallback(async () => {
    try {
      const [historyData, favData, playlistData] = await Promise.all([
        apiFetch<{ lesson_id: string }[]>("/api/library/history"),
        apiFetch<{ lesson_id: string }[]>("/api/library/favorites"),
        apiFetch<ApiPlaylist[]>("/api/library/playlists"),
      ]);

      setStudy({
        viewedLessons: historyData.map((item) => item.lesson_id),
        favoriteLessons: favData.map((item) => item.lesson_id),
        playlists: playlistData.map((p) => ({
          id: p.id,
          name: p.name,
          lessonIds: p.lesson_ids,
        })),
      });
      setError(null);
      setReady(true);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar biblioteca de estudo");
      setReady(true);
      return false;
    }
  }, []);

  useEffect(() => {
    void refreshFromBackend();
    const handleSync = () => {
      void refreshFromBackend();
    };
    window.addEventListener(LIBRARY_SYNC_EVENT, handleSync);
    return () => {
      window.removeEventListener(LIBRARY_SYNC_EVENT, handleSync);
    };
  }, [refreshFromBackend]);

  const recordLessonView = useCallback(
    async (lessonId: string) => {
      await apiFetch(`/api/library/history/${encodeURIComponent(lessonId)}`, {
        method: "POST",
      });
      await refreshFromBackend();
      window.dispatchEvent(new Event(LIBRARY_SYNC_EVENT));
    },
    [refreshFromBackend]
  );

  const toggleFavoriteLesson = useCallback(
    async (lessonId: string): Promise<boolean> => {
      const isFav = study.favoriteLessons.includes(lessonId);
      await apiFetch(`/api/library/favorites/${encodeURIComponent(lessonId)}`, {
        method: isFav ? "DELETE" : "POST",
      });
      await refreshFromBackend();
      window.dispatchEvent(new Event(LIBRARY_SYNC_EVENT));
      return !isFav;
    },
    [refreshFromBackend, study.favoriteLessons]
  );

  const createPlaylist = useCallback(
    async (name: string): Promise<boolean> => {
      const trimmed = name.trim();
      if (!trimmed) return false;
      await apiFetch<ApiPlaylist>("/api/library/playlists", {
        method: "POST",
        body: JSON.stringify({ name: trimmed }),
      });
      await refreshFromBackend();
      window.dispatchEvent(new Event(LIBRARY_SYNC_EVENT));
      return true;
    },
    [refreshFromBackend]
  );

  const updatePlaylistLessons = useCallback(
    async (playlistId: string, lessonIds: string[]): Promise<boolean> => {
      await apiFetch<ApiPlaylist>(
        `/api/library/playlists/${encodeURIComponent(playlistId)}/lessons`,
        {
          method: "PUT",
          body: JSON.stringify({ lesson_ids: lessonIds }),
        }
      );
      await refreshFromBackend();
      window.dispatchEvent(new Event(LIBRARY_SYNC_EVENT));
      return true;
    },
    [refreshFromBackend]
  );

  const saveStudy = useCallback((nextStudy: StudyDemo = initialStudyDemo) => {
    setStudy(nextStudy);
    return true;
  }, []);

  return {
    study,
    saveStudy,
    ready,
    error,
    usingBackend: error === null,
    recordLessonView,
    toggleFavoriteLesson,
    createPlaylist,
    updatePlaylistLessons,
  };
}
