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


# Staff-only views for member management

def check_staff_permission(request):
    """Check if the logged-in user is staff."""
    if 'user_id' not in request.session:
        return False
    user_type = request.session.get('user_type')
    return user_type == 'staff'


@csrf_exempt
def add_member(request):
    """
    Add a new member (student). Staff only.
    """
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['name', 'email', 'phone', 'username', 'password']
            for field in required_fields:
                if not data.get(field):
                    response = JsonResponse({'error': f'{field} is required'}, status=400)
                    return add_cors_headers(response)
            
            # Check if username already exists
            if User.objects.filter(Username=data['username']).exists():
                response = JsonResponse({'error': 'Username already exists'}, status=400)
                return add_cors_headers(response)
            
            # Create user
            user = User.objects.create(
                Name=data['name'],
                Email=data['email'],
                Phone=data['phone'],
                Username=data['username'],
                Password=data['password'],  # In production, hash this
                Type='student'
            )
            
            # Create student record
            student = Student.objects.create(user=user)
            
            response = JsonResponse({
                'success': True,
                'message': 'Member added successfully',
                'member': {
                    'user_id': user.User_ID,
                    'name': user.Name,
                    'email': user.Email,
                    'phone': user.Phone,
                    'username': user.Username
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


def search_members(request):
    """
    Search members by name, email, or phone. Staff only.
    """
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    query = request.GET.get('q', '').strip()
    
    if query:
        from django.db.models import Q
        users = User.objects.filter(
            Type='student'
        ).filter(
            Q(Name__icontains=query) |
            Q(Email__icontains=query) |
            Q(Phone__icontains=query) |
            Q(Username__icontains=query)
        )
    else:
        # Return all students if no query
        users = User.objects.filter(Type='student')
    
    results = []
    for user in users:
        results.append({
            'user_id': user.User_ID,
            'name': user.Name,
            'email': user.Email,
            'phone': user.Phone,
            'username': user.Username
        })
    
    response = JsonResponse({
        'results': results,
        'count': len(results)
    })
    return add_cors_headers(response)


@csrf_exempt
def delete_member(request, user_id):
    """
    Delete a member. Staff only.
    Cannot delete if member has active borrows or unpaid fines.
    """
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    if request.method == 'DELETE':
        try:
            user = User.objects.get(User_ID=user_id, Type='student')
            student = Student.objects.get(user=user)
            
            # Check for active borrows
            active_borrows = Borrow.objects.filter(
                student=student,
                status__in=['active', 'late']
            ).count()
            
            if active_borrows > 0:
                response = JsonResponse({
                    'error': 'Cannot delete member with active borrows'
                }, status=400)
                return add_cors_headers(response)
            
            # Check for unpaid fines
            unpaid_fines = Fine.objects.filter(
                Student_ID=student,
                Status='unpaid'
            ).count()
            
            if unpaid_fines > 0:
                response = JsonResponse({
                    'error': 'Cannot delete member with unpaid fines'
                }, status=400)
                return add_cors_headers(response)
            
            # Delete student and user
            student.delete()
            user.delete()
            
            response = JsonResponse({
                'success': True,
                'message': 'Member deleted successfully'
            })
            return add_cors_headers(response)
            
        except User.DoesNotExist:
            response = JsonResponse({'error': 'Member not found'}, status=404)
            return add_cors_headers(response)
        except Student.DoesNotExist:
            response = JsonResponse({'error': 'Student record not found'}, status=404)
            return add_cors_headers(response)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=500)
            return add_cors_headers(response)
    
    response = JsonResponse({'error': 'DELETE method required'}, status=405)
    return add_cors_headers(response)


def get_all_members(request):
    """
    Get all members with their statistics. Staff only.
    """
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    students = Student.objects.all().select_related('user')
    
    results = []
    for student in students:
        # Get statistics
        active_borrows = Borrow.objects.filter(
            student=student,
            status__in=['active', 'late']
        ).count()
        
        total_borrows = Borrow.objects.filter(student=student).count()
        
        unpaid_fines = Fine.objects.filter(
            Student_ID=student,
            Status='unpaid'
        ).count()
        
        results.append({
            'user_id': student.user.User_ID,
            'name': student.user.Name,
            'email': student.user.Email,
            'phone': student.user.Phone,
            'username': student.user.Username,
            'active_borrows': active_borrows,
            'total_borrows': total_borrows,
            'unpaid_fines': unpaid_fines
        })
    
    response = JsonResponse({
        'results': results,
        'count': len(results)
    })
    return add_cors_headers(response)

