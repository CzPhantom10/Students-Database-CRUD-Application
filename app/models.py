import re
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "John Doe"})
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format", json_schema_extra={"example": "2004-05-15"})
    email: str = Field(..., json_schema_extra={"example": "john.doe@example.com"})
    phone: str = Field(..., min_length=7, max_length=20, json_schema_extra={"example": "+1-555-0199"})
    course: Optional[str] = Field(None, max_length=100, json_schema_extra={"example": "Computer Science"})
    address: Optional[str] = Field(None, max_length=255, json_schema_extra={"example": "123 Academic Way, Apt 4B"})
    enrollment_date: Optional[str] = Field(
        default_factory=lambda: str(date.today()),
        description="Enrollment date in YYYY-MM-DD format (defaults to current date)",
        json_schema_extra={"example": "2024-09-01"}
    )

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v_clean = v.strip()
        if not EMAIL_REGEX.match(v_clean):
            raise ValueError("Invalid email address format.")
        return v_clean.lower()

    @field_validator("dob")
    @classmethod
    def validate_dob_format(cls, v: str) -> str:
        try:
            date.fromisoformat(v.strip())
        except ValueError:
            raise ValueError("dob must be a valid date in YYYY-MM-DD format.")
        return v.strip()


class StudentCreate(StudentBase):
    student_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Unique student identifier. If omitted, will be auto-generated.",
        json_schema_extra={"example": "STU-1001"}
    )


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    dob: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    email: Optional[str] = None
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[str] = Field(None, description="Enrollment date in YYYY-MM-DD format")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            if not EMAIL_REGEX.match(v_clean):
                raise ValueError("Invalid email address format.")
            return v_clean.lower()
        return v

    @field_validator("dob")
    @classmethod
    def validate_dob_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                date.fromisoformat(v.strip())
            except ValueError:
                raise ValueError("dob must be a valid date in YYYY-MM-DD format.")
            return v.strip()
        return v


class StudentResponse(StudentBase):
    student_id: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
    student_id: Optional[str] = None


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, json_schema_extra={"example": "How many students are enrolled in Computer Science?"})
    provider: Optional[str] = Field("g4f", description="AI provider: 'g4f' (free cloud LLM, no local setup needed) or 'ollama' (local LLM)", json_schema_extra={"example": "g4f"})
    model: Optional[str] = Field("auto", description="Model name (e.g., 'auto', 'gpt-4o-mini' for g4f, or 'llama3.2:1b' for ollama)", json_schema_extra={"example": "auto"})


class AIQueryResponse(BaseModel):
    question: str
    answer: str
    context_records_count: int
    provider: str
    model_used: str
    status: str
