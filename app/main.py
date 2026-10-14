import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from app.ai_service import query_ai
from app.database import (
    delete_student,
    get_all_records_for_context,
    get_student_by_id,
    init_db,
    insert_student,
    list_students,
    update_student,
)
from app.models import (
    AIQueryRequest,
    AIQueryResponse,
    MessageResponse,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Students Database CRUD API",
    description="FastAPI backend application for managing student records with SQLite persistent storage and an optional AI extension.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def root():
    return {
        "message": "Welcome to the Students Database CRUD API",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "create_student": "POST /students",
            "list_students": "GET /students",
            "get_student": "GET /students/{student_id}",
            "update_student": "PUT / PATCH /students/{student_id}",
            "delete_student": "DELETE /students/{student_id}",
            "ai_query": "POST /students/ai-query"
        }
    }


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "ok", "database": "sqlite"}


@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Students"],
    summary="Create a new student record"
)
def create_student(payload: StudentCreate):
    student_id = payload.student_id or f"STU-{uuid.uuid4().hex[:6].upper()}"

    if get_student_by_id(student_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with ID '{student_id}' already exists."
        )

    data = payload.model_dump()
    data["student_id"] = student_id
    record = insert_student(data)
    return record


@app.get(
    "/students",
    response_model=List[StudentResponse],
    tags=["Students"],
    summary="List all students with optional filtering and pagination"
)
def get_students(
    course: Optional[str] = Query(None, description="Filter by course name (case-insensitive)"),
    search: Optional[str] = Query(None, description="Search across student name or email"),
    born_after: Optional[str] = Query(None, description="Filter students born on or after YYYY-MM-DD"),
    born_before: Optional[str] = Query(None, description="Filter students born on or before YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    return list_students(
        course=course,
        search=search,
        born_after=born_after,
        born_before=born_before,
        limit=limit,
        offset=offset
    )


@app.get(
    "/students/{student_id}",
    response_model=StudentResponse,
    tags=["Students"],
    summary="Retrieve a single student by student_id"
)
def get_student(student_id: str):
    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' not found."
        )
    return student


@app.put(
    "/students/{student_id}",
    response_model=StudentResponse,
    tags=["Students"],
    summary="Update an existing student's details"
)
def update_student_full(student_id: str, payload: StudentUpdate):
    existing = get_student_by_id(student_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' not found."
        )

    updated = update_student(student_id, payload.model_dump(exclude_unset=True))
    return updated


@app.patch(
    "/students/{student_id}",
    response_model=StudentResponse,
    tags=["Students"],
    summary="Partially update an existing student's details"
)
def patch_student(student_id: str, payload: StudentUpdate):
    return update_student_full(student_id, payload)


@app.delete(
    "/students/{student_id}",
    response_model=MessageResponse,
    tags=["Students"],
    summary="Delete a student record"
)
def remove_student(student_id: str):
    success = delete_student(student_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' not found."
        )
    return MessageResponse(
        message=f"Student '{student_id}' successfully deleted.",
        student_id=student_id
    )


@app.post(
    "/students/ai-query",
    response_model=AIQueryResponse,
    tags=["AI Extension"],
    summary="Ask natural language questions about student data (Supports g4f & Ollama)"
)
def ask_ai(payload: AIQueryRequest):
    records = get_all_records_for_context()
    result = query_ai(
        question=payload.question,
        records=records,
        provider=payload.provider or "g4f",
        model=payload.model or "auto"
    )
    return AIQueryResponse(
        question=payload.question,
        answer=result["answer"],
        context_records_count=result["context_records_count"],
        provider=result.get("provider", payload.provider or "g4f"),
        model_used=result.get("model_used", payload.model or "auto"),
        status=result["status"]
    )
