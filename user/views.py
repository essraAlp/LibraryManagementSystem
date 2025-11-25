from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
from .models import User, Student, Staff
from Barrow.models import Borrow
from fine.models import Fine
import json

# Create your views here.

def add_cors_headers(response):
    """Add CORS headers to response"""
    response['Access-Control-Allow-Origin'] = 'http://localhost:8080'
    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    response['Access-Control-Allow-Credentials'] = 'true'
    return response

@csrf_exempt
def login_view(request):
    """
    Handle user login with username and password.
    """
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                response = JsonResponse({'error': 'Username and password are required'}, status=400)
                return add_cors_headers(response)
            
            try:
                user = User.objects.get(Username=username)
                
                # Simple password check (you should use hashed passwords in production)
                if user.Password == password:
                    # Store user info in session
                    request.session['user_id'] = user.User_ID
                    request.session['user_type'] = user.Type
                    request.session['username'] = user.Username
                    
                    response = JsonResponse({
                        'success': True,
                        'user_id': user.User_ID,
                        'name': user.Name,
                        'type': user.Type
                    })
                    return add_cors_headers(response)
                else:
                    response = JsonResponse({'error': 'Invalid credentials'}, status=401)
                    return add_cors_headers(response)
                    
            except User.DoesNotExist:
                response = JsonResponse({'error': 'Invalid credentials'}, status=401)
                return add_cors_headers(response)
                
        except json.JSONDecodeError:
            response = JsonResponse({'error': 'Invalid JSON'}, status=400)
            return add_cors_headers(response)
    
    response = JsonResponse({'error': 'POST method required'}, status=405)
    return add_cors_headers(response)


@csrf_exempt
def logout_view(request):
    """
    Handle user logout.
    """
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    request.session.flush()
    response = JsonResponse({'success': True, 'message': 'Logged out successfully'})
    return add_cors_headers(response)


def check_session(request):
    """
    Check if user is logged in.
    """
    if 'user_id' in request.session:
        try:
            user = User.objects.get(User_ID=request.session['user_id'])
            response = JsonResponse({
                'logged_in': True,
                'user_id': user.User_ID,
                'name': user.Name,
                'type': user.Type,
                'username': user.Username
            })
            return add_cors_headers(response)
        except User.DoesNotExist:
            request.session.flush()
            response = JsonResponse({'logged_in': False})
            return add_cors_headers(response)
    
    response = JsonResponse({'logged_in': False})
    return add_cors_headers(response)


def get_member_borrowings(request):
    """
    Get borrowing history for logged-in member.
    Includes past borrowings, active borrowings with return dates, and fine status.
    """
    if 'user_id' not in request.session or request.session.get('user_type') != 'student':
        response = JsonResponse({'error': 'Unauthorized'}, status=401)
        return add_cors_headers(response)
    
    user_id = request.session['user_id']
    
    try:
        student = Student.objects.get(user__User_ID=user_id)
        
        # Get all borrowings
        borrowings = Borrow.objects.filter(student=student).order_by('-date')
        
        results = []
        for borrow in borrowings:
            # Get fine information if exists
            fines = Fine.objects.filter(Student_ID=student, Borrow_ID=borrow)
            
            fine_info = None
            if fines.exists():
                fine = fines.first()
                fine_info = {
                    'amount': fine.Amount,
                    'status': fine.Status,
                    'date': fine.Date.strftime('%Y-%m-%d'),
                    'payment_date': fine.Payment_Date.strftime('%Y-%m-%d') if fine.Payment_Date else None
                }
            
            results.append({
                'borrow_id': borrow.Borrow_ID,
                'book': {
                    'isbn': borrow.book.ISBN,
                    'name': borrow.book.name,
                    'author': borrow.book.author,
                    'image': borrow.book.image
                },
                'borrow_date': borrow.date.strftime('%Y-%m-%d'),
                'last_return_date': borrow.last_date.strftime('%Y-%m-%d'),
                'status': borrow.status,
                'fine': fine_info
            })
        
        response = JsonResponse({'borrowings': results, 'count': len(results)})
        return add_cors_headers(response)
        
    except Student.DoesNotExist:
        response = JsonResponse({'error': 'Student not found'}, status=404)
        return add_cors_headers(response)


def get_member_profile(request):
    """
    Get member profile information.
    """
    if 'user_id' not in request.session:
        response = JsonResponse({'error': 'Unauthorized'}, status=401)
        return add_cors_headers(response)
    
    user_id = request.session['user_id']
    
    try:
        user = User.objects.get(User_ID=user_id)
        
        response = JsonResponse({
            'user_id': user.User_ID,
            'name': user.Name,
            'email': user.Email,
            'phone': user.Phone,
            'username': user.Username,
            'type': user.Type
        })
        return add_cors_headers(response)
        
    except User.DoesNotExist:
        response = JsonResponse({'error': 'User not found'}, status=404)
        return add_cors_headers(response)


@csrf_exempt
def update_member_profile(request):
    """
    Update member profile (email, phone, password only).
    """
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    if request.method != 'POST':
        response = JsonResponse({'error': 'POST method required'}, status=405)
        return add_cors_headers(response)
    
    if 'user_id' not in request.session:
        response = JsonResponse({'error': 'Unauthorized'}, status=401)
        return add_cors_headers(response)
    
    user_id = request.session['user_id']
    
    try:
        data = json.loads(request.body)
        user = User.objects.get(User_ID=user_id)
        
        # Update allowed fields
        if 'email' in data:
            user.Email = data['email']
        
        if 'phone' in data:
            user.Phone = data['phone']
        
        if 'password' in data and data['password']:
            user.Password = data['password']  # In production, hash this password
        
        user.save()
        
        response = JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'email': user.Email,
                'phone': user.Phone
            }
        })
        return add_cors_headers(response)
        
    except User.DoesNotExist:
        response = JsonResponse({'error': 'User not found'}, status=404)
        return add_cors_headers(response)
    except json.JSONDecodeError:
        response = JsonResponse({'error': 'Invalid JSON'}, status=400)
        return add_cors_headers(response)
