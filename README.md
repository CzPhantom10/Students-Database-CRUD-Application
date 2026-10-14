# Students Database CRUD Application (+ Optional Ollama AI Extension)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-19%20Passing-success.svg)]()

> **EWB Edu Tech Pvt. Ltd. — Internship Project Assignment (Python Backend Development)**  
> Built with clean architecture, zero-bloat standard library SQLite persistence, robust input validation, and an optional local Ollama LLM integration for grounded natural language queries.

---

## Project Overview

This backend application provides a complete RESTful API to manage student records using Create, Read, Update, and Delete (**CRUD**) operations. Data is persistently stored in an **SQLite** database (`data/students.db`), and interactive API documentation is automatically provided via **Swagger UI** and **ReDoc**.

An optional **AI extension** supports both **g4f** (free cloud LLM, zero setup) and local **Ollama** (e.g., `llama3.2:1b`) to answer natural language questions (such as *"How many students are in Data Science?"* or *"List students born after 2004"*). To ensure security, the LLM is **never allowed to execute unrestricted SQL**; instead, sanitized records are retrieved by backend code and provided as grounded read-only context.

---

## Technology Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Server:** Uvicorn
- **Database:** SQLite3 (Python Standard Library with WAL mode & Row Factory)
- **Validation & Serialization:** Pydantic V2
- **Testing:** Pytest & HTTPX (TestClient)
- **AI Extension:** g4f (free cloud LLM) & Ollama (`llama3.2:1b`)

---

## Project Structure

```text
EWB Project 2/
├── app/
│   ├── __init__.py         # Package initialization
│   ├── database.py         # SQLite connection manager, table migrations, and queries
│   ├── models.py           # Pydantic schemas, regex validators, request/response models
│   ├── ai_service.py       # g4f and Ollama integration with grounded context & offline fallback
│   └── main.py             # FastAPI routing, lifespan setup, and error handlers
├── data/
│   └── students.db         # Persistent SQLite database file (created on launch)
├── tests/
│   ├── __init__.py
│   └── test_api.py         # Comprehensive test suite (19 automated tests)
├── sample_data.py          # Seeding script to populate realistic student records
├── requirements.txt        # Production & testing dependencies
├── .gitignore              # Ignores caches, virtual envs, and database files
└── README.md               # Complete setup, testing, and API documentation
```

---

## Student Record Fields

| Field | Type | Mandatory? | Description / Validation |
|---|---|---|---|
| `student_id` | `string` | **Yes** (Unique) | Unique identifier (e.g., `STU-1001` or auto-generated `STU-XXXXXX`) |
| `name` | `string` | **Yes** | Full student name (1 to 100 characters) |
| `dob` | `string` | **Yes** | Date of Birth in `YYYY-MM-DD` format |
| `email` | `string` | **Yes** | Valid email address (validated with regex) |
| `phone` | `string` | **Yes** | Contact phone number (7 to 20 characters) |
| `course` | `string` | Optional | Enrolled course (e.g., `Computer Science`, `Data Science`) |
| `address` | `string` | Optional | Residential address |
| `enrollment_date`| `string` | Optional | Enrollment date (`YYYY-MM-DD`), defaults to current date |
| `created_at` | `string` | Auto | UTC ISO timestamp when created |
| `updated_at` | `string` | Auto | UTC ISO timestamp when last updated |

---

## Getting Started

### 1. Prerequisites
- **Python 3.10** or higher installed ([python.org](https://www.python.org/))
- *(Optional)* [Ollama](https://ollama.com/) if using local models instead of default g4f

### 2. Setup Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Activate on Windows (CMD)
.venv\Scripts\activate.bat

# Activate on macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Seed Sample Data (Optional but Recommended)

Populate the database with 5 realistic sample student records:

```bash
python sample_data.py
```

### 5. Run the Server

```bash
uvicorn app.main:app --reload
```

The application starts at: **`http://127.0.0.1:8000`**

- **Interactive API Docs (Swagger UI):** [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **Alternative ReDoc UI:** [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)
- **Health Check:** [`http://127.0.0.1:8000/health`](http://127.0.0.1:8000/health)

---

## API Endpoints & Testing Instructions

### 1. Create a Student
- **Method:** `POST`
- **Endpoint:** `/students`
- **Status Code:** `201 Created` (or `409 Conflict` if `student_id` already exists)

```bash
curl -X POST "http://127.0.0.1:8000/students" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU-2001",
    "name": "Dev Sharma",
    "dob": "2005-06-15",
    "email": "dev.sharma@example.com",
    "phone": "+91-9876501234",
    "course": "Computer Science",
    "address": "Block B, Tech Park, Pune",
    "enrollment_date": "2024-08-15"
  }'
```

*(Note: If `"student_id"` is omitted, the API automatically generates a unique ID like `STU-A1B2C3`)*.

---

### 2. List & Filter Students
- **Method:** `GET`
- **Endpoint:** `/students`
- **Query Parameters:**
  - `course`: Filter by exact course name (case-insensitive)
  - `search`: Case-insensitive search on name or email
  - `born_after`: Filter students born on or after date (`YYYY-MM-DD`)
  - `born_before`: Filter students born on or before date (`YYYY-MM-DD`)
  - `limit`: Max records to return (default: `100`)
  - `offset`: Offset for pagination (default: `0`)

```bash
# List all students
curl -X GET "http://127.0.0.1:8000/students"

# Filter by course
curl -X GET "http://127.0.0.1:8000/students?course=Computer%20Science"

# Filter students born after 2005
curl -X GET "http://127.0.0.1:8000/students?born_after=2005-01-01"

# Search by keyword
curl -X GET "http://127.0.0.1:8000/students?search=Priya"
```

---

### 3. Retrieve Individual Student Profile
- **Method:** `GET`
- **Endpoint:** `/students/{student_id}`
- **Status Code:** `200 OK` (or `404 Not Found`)

```bash
curl -X GET "http://127.0.0.1:8000/students/STU-1001"
```

---

### 4. Update Student Details
- **Method:** `PUT` or `PATCH`
- **Endpoint:** `/students/{student_id}`
- **Status Code:** `200 OK` (or `404 Not Found`)

```bash
curl -X PATCH "http://127.0.0.1:8000/students/STU-1001" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+91-9999888877",
    "course": "Artificial Intelligence"
  }'
```

---

### 5. Delete Student Record
- **Method:** `DELETE`
- **Endpoint:** `/students/{student_id}`
- **Status Code:** `200 OK` (or `404 Not Found`)

```bash
curl -X DELETE "http://127.0.0.1:8000/students/STU-2001"
```

---

### 6. AI Extension (g4f & Ollama supported)
- **Method:** `POST`
- **Endpoint:** `/students/ai-query`
- **Status Code:** `200 OK`

You can use either **`g4f` (free cloud LLM, zero setup, no Ollama needed)** or **`ollama` (local LLM)**:

#### Option A: Using `g4f` (Default - No Local Installation Needed)
```bash
curl -X POST "http://127.0.0.1:8000/students/ai-query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many students are enrolled in Computer Science?",
    "provider": "g4f",
    "model": "auto"
  }'
```

#### Option B: Using Local `ollama` (Assignment Bonus Specification)
```bash
curl -X POST "http://127.0.0.1:8000/students/ai-query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many students are there, and who was born after 2005?",
    "provider": "ollama",
    "model": "llama3.2:1b"
  }'
```

#### Running Ollama Locally:
1. Download Ollama from [ollama.com](https://ollama.com).
2. Pull and run the model:
   ```bash
   ollama run llama3.2:1b
   ```
3. *Graceful Fallback:* If Ollama is offline and requested, the API returns a helpful notification rather than crashing.

---

## Running Automated Tests

Run the comprehensive pytest test suite covering all 4 CRUD operations, validation rules, 404/409 error handling, and AI queries:

```bash
python -m pytest -v
```

Expected output:
```text
tests/test_api.py::test_root_endpoint PASSED                      [  5%]
tests/test_api.py::test_health_check PASSED                       [ 10%]
tests/test_api.py::test_create_student_with_id PASSED             [ 15%]
tests/test_api.py::test_create_student_autogen_id PASSED          [ 21%]
tests/test_api.py::test_create_duplicate_student_id PASSED        [ 26%]
tests/test_api.py::test_create_student_validation_error PASSED    [ 31%]
tests/test_api.py::test_get_all_students PASSED                   [ 36%]
tests/test_api.py::test_get_student_by_id PASSED                  [ 42%]
tests/test_api.py::test_get_student_not_found PASSED              [ 47%]
tests/test_api.py::test_filter_students_by_course PASSED          [ 52%]
tests/test_api.py::test_filter_students_by_dob PASSED             [ 57%]
tests/test_api.py::test_search_students PASSED                    [ 63%]
tests/test_api.py::test_update_student_put PASSED                 [ 68%]
tests/test_api.py::test_update_student_patch PASSED               [ 73%]
tests/test_api.py::test_update_student_not_found PASSED           [ 78%]
tests/test_api.py::test_delete_student PASSED                     [ 84%]
tests/test_api.py::test_delete_student_not_found PASSED           [ 89%]
tests/test_api.py::test_ai_query_offline_graceful_handling PASSED [ 94%]
tests/test_api.py::test_ai_query_g4f_handling PASSED              [100%]

============================= 19 passed in 4.75s ==============================
```

---

## Security & Data Integrity

- **SQL Injection Prevention:** Uses parameterized queries (`?` and `:key` binding) for all database operations.
- **AI Safety:** The LLM is never given SQL generation privileges or database access. Only sanitized records are provided to the model prompt as read-only context.
- **Privacy:** Dummy data is seeded for demonstration; no sensitive credentials, secrets, or real student personal information are included.

---

## Review Checklist Verification

- [x] **Create:** Adds new student records with unique ID check (`POST /students`).
- [x] **Read:** Lists all students, filters by course, DOB range, keyword search (`GET /students`), and retrieves single profile (`GET /students/{id}`).
- [x] **Update:** Updates existing details cleanly via `PUT` and `PATCH /students/{id}`.
- [x] **Delete:** Removes records with confirmation and handles missing IDs (`DELETE /students/{id}`).
- [x] **Persistence:** Data persists across app restarts in SQLite (`data/students.db`).
- [x] **Validation:** Pydantic models enforce email format, DOB format, phone number lengths, and required fields.
- [x] **Documentation:** Fully documented OpenAPI (`/docs`), curl instructions, and reproducible setup.
- [x] **Optional AI Extension:** Natural language Q&A grounded in retrieved records with g4f and Ollama.
