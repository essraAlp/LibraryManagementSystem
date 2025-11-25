"""
Script to list all students in the database with their credentials
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from user.models import User, Student

def list_students():
    print("=" * 80)
    print("Students in Database")
    print("=" * 80)
    
    students = Student.objects.all()
    
    if not students:
        print("No students found in database!")
        return
    
    print(f"\nFound {len(students)} students:\n")
    print(f"{'Name':<25} {'Username':<20} {'Password':<15} {'Email':<30}")
    print("-" * 80)
    
    for student in students:
        user = student.user
        print(f"{user.Name:<25} {user.Username:<20} {user.Password:<15} {user.Email:<30}")
    
    print("\n" + "=" * 80)
    print("Use any of the above username/password combinations to log in")
    print("=" * 80)

if __name__ == "__main__":
    list_students()
