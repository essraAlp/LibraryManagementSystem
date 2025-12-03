from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from .models import Borrow
from Books.models import Book
from user.models import Student, Staff, User
from fine.models import Fine
from datetime import date, datetime, timedelta
import json

# Create your views here.

def update_late_borrows():
    """Check and update overdue borrows to late status and create/update fines."""
    today = date.today()
    
    # Get ALL overdue borrows (both active and already late status)
    late_borrows = Borrow.objects.filter(
        status__in=['active', 'late'],
        last_date__lt=today
    ).select_related('book', 'student')
    
    for borrow in late_borrows:
        # Update status to late if it's still active
        if borrow.status == 'active':
            borrow.status = 'late'
            borrow.save()
        
        # Update book status to late if not already
        if borrow.book.status != 'late':
            borrow.book.status = 'late'
            borrow.book.save()
        
        # Calculate current fine amount
        days_late = (today - borrow.last_date).days
        fine_amount = days_late * 5.0  # 5 TL per day
        
        # Find existing unpaid fine for this borrow
        existing_fine = Fine.objects.filter(Borrow_ID=borrow, Status='unpaid').first()
        
        if existing_fine:
            # Update existing fine amount and date
            existing_fine.Amount = fine_amount
            existing_fine.Date = today
            existing_fine.save()
        else:
            # Create new fine if it doesn't exist
            try:
                staff = Staff.objects.first()
                if staff and borrow.student:
                    Fine.objects.create(
                        Staff_ID=staff,
                        Student_ID=borrow.student,
                        Borrow_ID=borrow,
                        Date=today,
                        Status='unpaid',
                        Amount=fine_amount
                    )
            except Exception:
                pass  # If no staff exists, skip fine creation

def add_cors_headers(response):
    """Add CORS headers to response"""
    response['Access-Control-Allow-Origin'] = 'http://localhost:8080'
    response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response['Access-Control-Allow-Credentials'] = 'true'
    return response


def check_staff_permission(request):
    """Check if the logged-in user is staff."""
    if 'user_id' not in request.session:
        return False
    user_type = request.session.get('user_type')
    return user_type == 'staff'


@csrf_exempt
def create_borrow(request):
    """
    Create a new borrow record. Staff only.
    """
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    if request.method == 'POST':
        try:
            # Update late borrows before creating new borrow
            update_late_borrows()
            
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['student_id', 'isbn', 'borrow_date', 'due_date']
            for field in required_fields:
                if not data.get(field):
                    response = JsonResponse({'error': f'{field} is required'}, status=400)
                    return add_cors_headers(response)
            
            # Get staff from session
            staff_user_id = request.session.get('user_id')
            try:
                staff = Staff.objects.get(user__User_ID=staff_user_id)
            except Staff.DoesNotExist:
                response = JsonResponse({'error': 'Staff not found'}, status=404)
                return add_cors_headers(response)
            
            # Get student
            try:
                student = Student.objects.get(user__User_ID=data['student_id'])
            except Student.DoesNotExist:
                response = JsonResponse({'error': 'Student not found'}, status=404)
                return add_cors_headers(response)
            
            # Get book
            try:
                book = Book.objects.get(ISBN=data['isbn'])
            except Book.DoesNotExist:
                response = JsonResponse({'error': 'Book not found'}, status=404)
                return add_cors_headers(response)
            
            # Check if book is available
            if book.status != 'available':
                response = JsonResponse({'error': 'Book is not available'}, status=400)
                return add_cors_headers(response)
            
            # Check maximum book limit (5 books per student)
            active_borrows_count = Borrow.objects.filter(
                student=student,
                status__in=['active', 'late']
            ).count()
            
            if active_borrows_count >= 5:
                response = JsonResponse({
                    'error': 'Bu üye zaten 5 kitap ödünç almış. Maksimum kitap limitine ulaşıldı.'
                }, status=400)
                return add_cors_headers(response)
            
            # Check unpaid fines limit (100 TL maximum)
            unpaid_fines_total = Fine.objects.filter(
                Student_ID=student,
                Status='unpaid'
            ).aggregate(total=Sum('Amount'))['total'] or 0
            
            if unpaid_fines_total >= 100:
                response = JsonResponse({
                    'error': f'Bu üyenin ödenmemiş cezası {unpaid_fines_total} TL. Limit 100 TL. Önce cezalarını ödemesi gerekiyor.'
                }, status=400)
                return add_cors_headers(response)
            
            # Parse dates
            try:
                borrow_date = datetime.strptime(data['borrow_date'], '%Y-%m-%d').date()
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            except ValueError:
                response = JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                return add_cors_headers(response)
            
            # Validate dates
            if due_date <= borrow_date:
                response = JsonResponse({'error': 'Due date must be after borrow date'}, status=400)
                return add_cors_headers(response)
            
            # Check maximum borrow duration (15 days)
            borrow_duration = (due_date - borrow_date).days
            if borrow_duration > 15:
                response = JsonResponse({
                    'error': 'Maksimum ödünç süresi 15 gündür. Lütfen daha kısa bir süre giriniz.'
                }, status=400)
                return add_cors_headers(response)
            
            # Create borrow record
            borrow = Borrow.objects.create(
                staff=staff,
                student=student,
                book=book,
                date=borrow_date,
                last_date=due_date,
                status='active'
            )
            
            # Update book status
            book.status = 'borrowed'
            book.save()
            
            response = JsonResponse({
                'success': True,
                'message': 'Borrow record created successfully',
                'borrow': {
                    'id': borrow.Borrow_ID,
                    'student_name': student.user.Name,
                    'book_name': book.name,
                    'borrow_date': borrow.date.strftime('%Y-%m-%d'),
                    'due_date': borrow.last_date.strftime('%Y-%m-%d'),
                    'status': borrow.status
                }
            })
            return add_cors_headers(response)
            
        except json.JSONDecodeError:
            response = JsonResponse({'error': 'Invalid JSON'}, status=400)
            return add_cors_headers(response)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=500)
            return add_cors_headers(response)
    
    response = JsonResponse({'error': 'POST method required'}, status=405)
    return add_cors_headers(response)


@csrf_exempt
def return_book(request, borrow_id):
    """
    Mark a book as returned. Staff only.
    """
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    if request.method == 'PUT':
        try:
            borrow = Borrow.objects.get(Borrow_ID=borrow_id)
            
            if borrow.status == 'returned':
                response = JsonResponse({'error': 'Book already returned'}, status=400)
                return add_cors_headers(response)
            
            # Check if book is late and create fine if necessary
            today = date.today()
            if today > borrow.last_date and borrow.status != 'returned':
                days_late = (today - borrow.last_date).days
                fine_amount = days_late * 5.0  # 5 TL per day
                
                staff_user_id = request.session.get('user_id')
                staff = Staff.objects.get(user__User_ID=staff_user_id)
                
                # Create fine if it doesn't exist
                if not Fine.objects.filter(Borrow_ID=borrow, Status='unpaid').exists():
                    Fine.objects.create(
                        Staff_ID=staff,
                        Student_ID=borrow.student,
                        Borrow_ID=borrow,
                        Date=today,
                        Status='unpaid',
                        Amount=fine_amount
                    )
            
            # Update borrow status
            borrow.status = 'returned'
            borrow.save()
            
            # Update book status
            book = borrow.book
            book.status = 'available'
            book.save()
            
            response = JsonResponse({
                'success': True,
                'message': 'Book returned successfully'
            })
            return add_cors_headers(response)
            
        except Borrow.DoesNotExist:
            response = JsonResponse({'error': 'Borrow record not found'}, status=404)
            return add_cors_headers(response)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=500)
            return add_cors_headers(response)
    
    response = JsonResponse({'error': 'PUT method required'}, status=405)
    return add_cors_headers(response)


def get_late_borrows(request):
    """
    Get all late borrows. Staff only.
    """
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    # Update late borrows first
    update_late_borrows()
    
    today = date.today()
    
    # Get all late borrows
    late_borrows = Borrow.objects.filter(
        status='late'
    ).select_related('student__user', 'book', 'staff__user')
    
    results = []
    for borrow in late_borrows:
        days_late = (today - borrow.last_date).days
        
        results.append({
            'borrow_id': borrow.Borrow_ID,
            'student_id': borrow.student.user.User_ID,
            'student_name': borrow.student.user.Name,
            'student_email': borrow.student.user.Email,
            'student_phone': borrow.student.user.Phone,
            'book_isbn': borrow.book.ISBN,
            'book_name': borrow.book.name,
            'book_author': borrow.book.author,
            'borrow_date': borrow.date.strftime('%Y-%m-%d'),
            'due_date': borrow.last_date.strftime('%Y-%m-%d'),
            'days_late': days_late,
            'status': borrow.status
        })
    
    response = JsonResponse({
        'results': results,
        'count': len(results)
    })
    return add_cors_headers(response)


def get_all_borrows(request):
    """
    Get all borrow records with filtering options. Staff only.
    """
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    # Get filter parameters
    status_filter = request.GET.get('status', None)
    student_id = request.GET.get('student_id', None)
    
    borrows = Borrow.objects.all().select_related('student__user', 'book', 'staff__user')
    
    if status_filter:
        borrows = borrows.filter(status=status_filter)
    
    if student_id:
        borrows = borrows.filter(student__user__User_ID=student_id)
    
    results = []
    for borrow in borrows:
        results.append({
            'borrow_id': borrow.Borrow_ID,
            'student_id': borrow.student.user.User_ID,
            'student_name': borrow.student.user.Name,
            'staff_name': borrow.staff.user.Name,
            'book_isbn': borrow.book.ISBN,
            'book_name': borrow.book.name,
            'borrow_date': borrow.date.strftime('%Y-%m-%d'),
            'due_date': borrow.last_date.strftime('%Y-%m-%d'),
            'status': borrow.status
        })
    
    response = JsonResponse({
        'results': results,
        'count': len(results)
    })
    return add_cors_headers(response)

