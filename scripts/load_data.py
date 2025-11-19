import csv
from django.conf import settings
from user.models import User, Student, Staff

STUDENT_CSV = "student.csv"
STAFF_CSV = "staff.csv"

def run():
    print("📌 Starting import...")

    # ----- IMPORT STAFF -----
    print("📘 Importing staff...")
    with open(STAFF_CSV, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            full_name = f"{row['name']} {row['surname']}"

            user = User.objects.create(
                Name=full_name,
                Email=row["email"],
                Phone=row["phone"],
                Username=row["username"],
                Password=row["password"],
                Type="staff"
            )

            Staff.objects.create(user=user)
            print(f"✔ Added staff: {user.Name}")

    # ----- IMPORT STUDENTS -----
    print("\n📗 Importing students...")
    with open(STUDENT_CSV, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:

            full_name = f"{row['name']} {row['surname']}"
            user = User.objects.create(
                Name=full_name,
                Email=row["email"],
                Phone=row["phone"],
                Username=row["username"],
                Password=row["password"],
                Type="student"
            )

            Student.objects.create(user=user)
            print(f"✔ Added student: {user.Name}")

    print("\n🎉 IMPORT FINISHED SUCCESSFULLY!")
