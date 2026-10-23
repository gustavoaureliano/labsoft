"""Domain exceptions raised by course operations."""


class CourseError(Exception):
    status_code = 400
    code = "course_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CourseNotFound(CourseError):
    status_code = 404
    code = "course_not_found"


class CourseForbidden(CourseError):
    status_code = 403
    code = "course_forbidden"


class CourseConflict(CourseError):
    status_code = 409
    code = "course_conflict"


class CourseValidationError(CourseError):
    status_code = 422
    code = "course_validation_error"


class MaterialNotFound(CourseError):
    status_code = 404
    code = "material_not_found"


class LessonNotFound(CourseError):
    status_code = 404
    code = "lesson_not_found"


class MediaNotFound(CourseError):
    status_code = 404
    code = "media_not_found"
