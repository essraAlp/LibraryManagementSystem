from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Fine
from user.models import Student, Staff
from datetime import date
import json

# Create your views here.

def add_cors_headers(response):
    """Add CORS headers to response"""
    response['Access-Control-Allow-Origin'] = 'http://localhost:8080'
    response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Access-Control-Allow-Credentials'] = 'true'
    return response


def check_staff_permission(request):
    """Check if the logged-in user is staff."""
    if 'user_id' not in request.session:
        return False
    user_type = request.session.get('user_type')
    return user_type == 'staff'


def get_all_fines(request):
    """
    Get all fines with filtering options. Staff only.
    """
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    # Get filter parameters
    status_filter = request.GET.get('status', None)
    student_id = request.GET.get('student_id', None)
    
    fines = Fine.objects.all().select_related('Student_ID__user', 'Staff_ID__user', 'Borrow_ID')
    
    if status_filter:
        fines = fines.filter(Status=status_filter)
    
    if student_id:
        fines = fines.filter(Student_ID__user__User_ID=student_id)
    
    results = []
    for fine in fines:
        results.append({
            'fine_id': fine.Fine_ID,
            'student_id': fine.Student_ID.user.User_ID,
            'student_name': fine.Student_ID.user.Name,
            'staff_name': fine.Staff_ID.user.Name,
            'borrow_id': fine.Borrow_ID.Borrow_ID if fine.Borrow_ID else None,
            'book_name': fine.Borrow_ID.book.name if fine.Borrow_ID else None,
            'date': fine.Date.strftime('%Y-%m-%d'),
            'amount': fine.Amount,
            'status': fine.Status,
            'payment_date': fine.Payment_Date.strftime('%Y-%m-%d') if fine.Payment_Date else None
        })
    
    response = JsonResponse({
        'results': results,
        'count': len(results)
    })
    return add_cors_headers(response)


@csrf_exempt
def mark_fine_paid(request, fine_id):
    """
    Mark a fine as paid. Staff only.
    """
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    if request.method == 'PUT':
        try:
            fine = Fine.objects.get(Fine_ID=fine_id)
            
            if fine.Status == 'paid':
                response = JsonResponse({'error': 'Fine already marked as paid'}, status=400)
                return add_cors_headers(response)
            
            # Update fine status
            fine.Status = 'paid'
            fine.Payment_Date = date.today()
            fine.save()
            
            response = JsonResponse({
                'success': True,
                'message': 'Fine marked as paid successfully'
            })
            return add_cors_headers(response)
            
        except Fine.DoesNotExist:
            response = JsonResponse({'error': 'Fine not found'}, status=404)
            return add_cors_headers(response)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=500)
            return add_cors_headers(response)
    
    response = JsonResponse({'error': 'PUT method required'}, status=405)
    return add_cors_headers(response)

