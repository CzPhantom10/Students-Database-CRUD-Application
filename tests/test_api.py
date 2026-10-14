import os
import tempfile
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_db_path = temp_db.name
temp_db.close()
os.environ["DATABASE_PATH"] = temp_db_path

from app.database import init_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
    yield
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data
    assert data["documentation"] == "/docs"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_student_with_id(client):
    payload = {
        "student_id": "TEST-101",
        "name": "Alice Wonder",
        "dob": "2004-03-12",
        "email": "alice@example.com",
        "phone": "+1-555-0100",
        "course": "Computer Science",
        "address": "100 Wonder Lane",
        "enrollment_date": "2024-01-10"
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == "TEST-101"
    assert data["name"] == "Alice Wonder"
    assert data["email"] == "alice@example.com"
    assert "created_at" in data
    assert "updated_at" in data


def test_create_student_autogen_id(client):
    payload = {
        "name": "Bob Builder",
        "dob": "2003-07-22",
        "email": "bob@example.com",
        "phone": "+1-555-0200",
        "course": "Mechanical Engineering"
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"].startswith("STU-")
    assert data["name"] == "Bob Builder"


def test_create_duplicate_student_id(client):
    payload = {
        "student_id": "TEST-101",
        "name": "Duplicate Alice",
        "dob": "2004-03-12",
        "email": "alice2@example.com",
        "phone": "+1-555-0100"
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_student_validation_error(client):
    payload = {
        "email": "invalid-email-format",
        "phone": "123"
    }
    response = client.post("/students", json=payload)
    assert response.status_code == 422


def test_get_all_students(client):
    response = client.get("/students")
    assert response.status_code == 200
    students = response.json()
    assert isinstance(students, list)
    assert len(students) >= 2


def test_get_student_by_id(client):
    response = client.get("/students/TEST-101")
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "TEST-101"
    assert data["name"] == "Alice Wonder"


def test_get_student_not_found(client):
    response = client.get("/students/NON-EXISTENT-ID")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_filter_students_by_course(client):
    response = client.get("/students?course=Computer Science")
    assert response.status_code == 200
    students = response.json()
    assert len(students) >= 1
    assert all(s["course"].lower() == "computer science" for s in students)


def test_filter_students_by_dob(client):
    response = client.get("/students?born_after=2004-01-01")
    assert response.status_code == 200
    students = response.json()
    assert all(s["dob"] >= "2004-01-01" for s in students)


def test_search_students(client):
    response = client.get("/students?search=Alice")
    assert response.status_code == 200
    students = response.json()
    assert len(students) == 1
    assert students[0]["student_id"] == "TEST-101"


def test_update_student_put(client):
    payload = {
        "name": "Alice Wonder Updated",
        "course": "Artificial Intelligence"
    }
    response = client.put("/students/TEST-101", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice Wonder Updated"
    assert data["course"] == "Artificial Intelligence"
    assert data["email"] == "alice@example.com"


def test_update_student_patch(client):
    payload = {"phone": "+1-555-9999"}
    response = client.patch("/students/TEST-101", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1-555-9999"
    assert data["name"] == "Alice Wonder Updated"


def test_update_student_not_found(client):
    response = client.patch("/students/MISSING-ID", json={"name": "Nobody"})
    assert response.status_code == 404


def test_delete_student(client):
    response = client.delete("/students/TEST-101")
    assert response.status_code == 200
    assert "successfully deleted" in response.json()["message"]

    get_res = client.get("/students/TEST-101")
    assert get_res.status_code == 404


def test_delete_student_not_found(client):
    response = client.delete("/students/TEST-101")
    assert response.status_code == 404


def test_ai_query_offline_graceful_handling(client):
    payload = {
        "question": "How many students are enrolled?",
        "provider": "ollama",
        "model": "llama3.2:1b"
    }
    response = client.post("/students/ai-query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "How many students are enrolled?"
    assert data["status"] in ["ollama_offline", "success", "error"]
    assert "context_records_count" in data


def test_ai_query_g4f_handling(client):
    with patch("app.main.query_ai") as mock_query:
        mock_query.return_value = {
            "answer": "There are 2 students in Computer Science.",
            "status": "success",
            "provider": "g4f",
            "model_used": "auto",
            "context_records_count": 5
        }
        payload = {
            "question": "How many students are in Computer Science?",
            "provider": "g4f",
            "model": "auto"
        }
        response = client.post("/students/ai-query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "How many students are in Computer Science?"
        assert data["status"] == "success"
        assert data["provider"] == "g4f"
        assert "Computer Science" in data["answer"]
