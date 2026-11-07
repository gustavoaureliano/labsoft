export type CourseStatus = "draft" | "published" | "archived";
export type AccessType = "free" | "paid";

export type ApiCourse = {
  id: string;
  teacher_id: string;
  teacher_name: string;
  title: string;
  subject: string;
  area: string;
  summary: string;
  exams: string[];
  access_type: AccessType;
  price: string | number | null;
  cover_media_id: string | null;
  status: CourseStatus;
  featured: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ApiCourseSummary = ApiCourse & {
  lesson_count: number;
  student_count: number;
  rating: number | null;
};

export type ApiLesson = {
  id: string;
  course_id: string;
  title: string;
  summary: string;
  duration_minutes: number;
  position: number;
  video_media_id: string | null;
  preview_available: boolean;
};

export type ApiMaterial = {
  id: string;
  course_id: string;
  lesson_id: string | null;
  media_id: string | null;
  title: string;
  description: string;
  kind: string;
  external_url: string | null;
  access_level: "public" | "enrolled";
  position: number;
  download_url: string | null;
  authorized: boolean;
};

export type ApiPagination = {
  page: number;
  size: number;
  total: number;
  pages: number;
};

export type ApiCoursePage = {
  items: ApiCourseSummary[];
  pagination: ApiPagination;
};

export type ApiAccess = {
  allowed: boolean;
  reason: string;
  acquisition_required: boolean;
};

export type ApiCourseDetails = {
  course: ApiCourseSummary;
  access: ApiAccess;
  lessons: ApiLesson[];
  reviews: Array<{ rating: number; comment: string; created_at: string }>;
};

export type ApiLanding = {
  sample_courses: ApiCourseSummary[];
  featured_courses: ApiCourseSummary[];
  access_options: string[];
};

export type ApiSearch = {
  courses: ApiCourseSummary[];
  materials: ApiMaterial[];
  total: number;
};

export type ApiRecommendation = {
  items: ApiCourseSummary[];
  strategy: string;
};

export type ApiMaterialList = {
  course_id: string;
  access: ApiAccess;
  items: ApiMaterial[];
};

export type ApiTeacherCourse = ApiCourseSummary & {
  material_count: number;
};

export type ApiTeacherDashboard = {
  items: ApiTeacherCourse[];
  total_courses: number;
  published_courses: number;
  draft_courses: number;
  total_students: number;
};

export type ApiCoursePreview = {
  course: ApiCourse;
  lessons: ApiLesson[];
  materials: ApiMaterial[];
  publication_pending: string[];
};
