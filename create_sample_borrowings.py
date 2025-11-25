"""
Script to create sample borrowing records for testing
"""
import os
import sys
import django
from datetime import date, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from user.models import User, Student, Staff
from Books.models import Book
from Barrow.models import Borrow
from fine.models import Fine

def create_sample_borrowings():
    print("=" * 60)
    print("Creating Sample Borrowing Records")
    print("=" * 60)
    
    # Get some students
    students = Student.objects.all()[:5]
    if not students:
        print("ERROR: No students found in database!")
        return
    
    print(f"Found {len(students)} students")
    
    # Get some staff members
    staff_members = Staff.objects.all()
    if not staff_members:
        print("ERROR: No staff found in database!")
        return
    
    staff = staff_members.first()
    print(f"Using staff: {staff.user.Name}")
    
    # Get some books
    books = Book.objects.all()[:20]
    if not books:
        print("ERROR: No books found in database!")
        return
    
    print(f"Found {len(books)} books")
    print()
    
    borrowings_created = 0
    fines_created = 0
    
    for student in students:
        print(f"\nCreating borrowings for student: {student.user.Name}")
        
        # Create 3-5 borrowings per student
        num_borrowings = random.randint(3, 5)
        student_books = random.sample(list(books), min(num_borrowings, len(books)))
        
        for i, book in enumerate(student_books):
            # Create different types of borrowings
            days_ago = random.randint(10, 90)
            borrow_date = date.today() - timedelta(days=days_ago)
            
            if i == 0:
                # Active borrowing
                status = 'active'
                last_date = date.today() + timedelta(days=7)
                print(f"  ✓ Active: {book.name[:40]} (due in 7 days)")
                
            elif i == 1 and random.random() > 0.5:
                # Late borrowing
                status = 'late'
                last_date = date.today() - timedelta(days=3)
                print(f"  ⚠ Late: {book.name[:40]} (overdue by 3 days)")
                
            else:
                # Returned borrowing
                status = 'returned'
                last_date = borrow_date + timedelta(days=14)
                print(f"  ✓ Returned: {book.name[:40]}")
            
            # Create borrowing
            borrow = Borrow.objects.create(
                staff=staff,
                student=student,
                book=book,
                status=status,
                date=borrow_date,
                last_date=last_date
            )
            borrowings_created += 1
            
            # Create fine for late borrowings (50% chance)
            if status == 'late' or (status == 'returned' and random.random() > 0.7):
                days_late = random.randint(1, 10)
                fine_amount = days_late * 5.0  # 5 TL per day
                fine_date = last_date + timedelta(days=1)
                
                # Determine if fine is paid
                fine_status = 'paid' if status == 'returned' else 'unpaid'
                payment_date = fine_date + timedelta(days=random.randint(1, 5)) if fine_status == 'paid' else None
                
                fine = Fine.objects.create(
                    Staff_ID=staff,
                    Student_ID=student,
                    Borrow_ID=borrow,
                    Date=fine_date,
                    Status=fine_status,
                    Payment_Date=payment_date,
                    Amount=fine_amount
                )
                fines_created += 1
                
                if fine_status == 'paid':
                    print(f"    💰 Fine: {fine_amount} TL (PAID on {payment_date})")
                else:
                    print(f"    💰 Fine: {fine_amount} TL (UNPAID)")
    
    print()
    print("=" * 60)
    print(f"✓ Created {borrowings_created} borrowing records")
    print(f"✓ Created {fines_created} fine records")
    print("=" * 60)
    print()
    print("Sample data created successfully!")
    print("You can now test the borrowing history and profile features.")

if __name__ == "__main__":
    try:
        create_sample_borrowings()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
