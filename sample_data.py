from app.database import init_db, insert_student, get_student_by_id

SAMPLE_STUDENTS = [
    {
        "student_id": "STU-1001",
        "name": "Aarav Sharma",
        "dob": "2003-08-14",
        "email": "aarav.sharma@example.com",
        "phone": "+91-9876543210",
        "course": "Computer Science",
        "address": "45 Park Street, New Delhi",
        "enrollment_date": "2023-08-01"
    },
    {
        "student_id": "STU-1002",
        "name": "Priya Patel",
        "dob": "2004-11-20",
        "email": "priya.patel@example.com",
        "phone": "+91-9822334455",
        "course": "Data Science",
        "address": "12 Ring Road, Ahmedabad",
        "enrollment_date": "2024-01-15"
    },
    {
        "student_id": "STU-1003",
        "name": "Rohan Gupta",
        "dob": "2006-02-10",
        "email": "rohan.gupta@example.com",
        "phone": "+91-9711223344",
        "course": "Computer Science",
        "address": "88 MG Road, Bengaluru",
        "enrollment_date": "2024-07-20"
    },
    {
        "student_id": "STU-1004",
        "name": "Sneha Nair",
        "dob": "2005-09-05",
        "email": "sneha.nair@example.com",
        "phone": "+91-9655443322",
        "course": "Cyber Security",
        "address": "21 Marine Lines, Mumbai",
        "enrollment_date": "2023-11-10"
    },
    {
        "student_id": "STU-1005",
        "name": "Kavya Singh",
        "dob": "2007-04-18",
        "email": "kavya.singh@example.com",
        "phone": "+91-9544332211",
        "course": "Data Science",
        "address": "7 Gandhi Nagar, Jaipur",
        "enrollment_date": "2024-08-01"
    }
]


def seed_database():
    init_db()
    inserted = 0
    for student in SAMPLE_STUDENTS:
        if not get_student_by_id(student["student_id"]):
            insert_student(student)
            inserted += 1
            print(f"Inserted: {student['student_id']} - {student['name']}")
        else:
            print(f"Skipped existing: {student['student_id']}")
    print(f"\nDone! Seeded {inserted} sample student records.")


if __name__ == "__main__":
    seed_database()
