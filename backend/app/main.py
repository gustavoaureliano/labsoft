from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.courses.exceptions import CourseError
from app.courses.router import router as courses_router

app = FastAPI(title="AprovaAí API")
app.include_router(courses_router)


@app.exception_handler(CourseError)
async def course_error_handler(_: Request, error: CourseError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": {"code": error.code, "message": error.message}},
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
