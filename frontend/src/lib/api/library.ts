import type { Course, Lesson } from "./learning";
import { useDemoStorage } from "@/lib/useDemoStorage";
import { initialStudyDemo, studyDemoKey } from "@/data/studyDemo";
import { isApiConfigured } from "@/lib/apiClient";
import { useStudyLibrary } from "@/lib/engagementApi";

export function useLibrary() {
  const [demo, saveDemo, demoReady] = useDemoStorage(studyDemoKey, initialStudyDemo);
  const remote = useStudyLibrary(isApiConfigured);
  if (isApiConfigured) return {
    study: remote.study, ready: remote.ready, error: remote.error,
    saveStudy: remote.saveStudy, recordLessonView: remote.recordLessonView,
    toggleFavoriteLesson: remote.toggleFavoriteLesson,
    updatePlaylistLessons: remote.updatePlaylistLessons, createPlaylist: remote.createPlaylist,
  };
  return {study: demo, ready: demoReady, error: null, saveStudy: saveDemo,
    recordLessonView: undefined, toggleFavoriteLesson: undefined,
    updatePlaylistLessons: undefined, createPlaylist: undefined};
}

// Browser-local library remains the other domain's demo adapter.
// Unknown/old IDs are retained in storage and never remapped to different lessons.
export function resolveLessons(ids: string[], courses: Course[]): Lesson[] {
  const lessons = new Map(courses.flatMap(course => course.lessons).map(lesson => [lesson.id, lesson]));
  return ids.flatMap(id => {const lesson = lessons.get(id); return lesson ? [lesson] : [];});
}
