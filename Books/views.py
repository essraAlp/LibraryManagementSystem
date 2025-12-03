from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from .models import Book
from Barrow.models import Borrow
from datetime import date
import logging
import json

# Create your views here.

logger = logging.getLogger(__name__)

def update_late_borrows():
    """Check and update overdue borrows to late status and create/update fines."""
    from fine.models import Fine
    from user.models import Staff
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

def search_books(request):
    """
    Search books by name, author, type, or publisher.
    Returns book details with availability status.
    Supports pagination with limit parameter.
    """
    query = request.GET.get('q', '').strip()
    
    logger.info(f"[SEARCH] Search request received with query: '{query}'")
    
    if not query:
        logger.warning("[SEARCH] Empty query received")
        return JsonResponse({'error': 'Search query is required'}, status=400)
    
    # Get pagination parameters
    try:
        limit = int(request.GET.get('limit', 50))  # Default to 50 results (reduced from 100)
        offset = int(request.GET.get('offset', 0))
        logger.info(f"[SEARCH] Pagination: limit={limit}, offset={offset}")
    except ValueError:
        limit = 50
        offset = 0
    
    # Limit maximum results to prevent large responses
    limit = min(limit, 50)  # Cap at 50 instead of 200
    
    logger.info(f"[SEARCH] Querying database for books matching: '{query}'")
    
    # Search across multiple fields
    all_books = Book.objects.filter(
        Q(name__icontains=query) |
        Q(author__icontains=query) |
        Q(type__icontains=query) |
        Q(publisher__icontains=query)
    )
    
    total_count = all_books.count()
    logger.info(f"[SEARCH] Found {total_count} total matching books")
    
    books = all_books[offset:offset + limit]
    logger.info(f"[SEARCH] Returning {len(books)} books (from offset {offset})")
    
    results = []
    logger.info(f"[SEARCH] Processing {len(books)} books to get availability info")
    
    for i, book in enumerate(books):
        if i % 20 == 0:  # Log every 20th book
            logger.info(f"[SEARCH] Processing book {i+1}/{len(books)}")
        
        # Check availability
        availability_info = get_book_availability(book.ISBN)
        
        results.append({
            'isbn': book.ISBN,
            'name': book.name[:100] if book.name else '',  # Truncate long names
            'author': book.author[:50] if book.author else '',  # Truncate long author names
            'publisher': book.publisher[:50] if book.publisher else '',
            'type': book.type[:30] if book.type else '',
            'year': book.year.strftime('%Y') if book.year else None,
            'explanation': book.explanation[:200] if book.explanation else '',  # Truncate explanation
            'image': book.image[:100] if book.image else '',
            'status': book.status,
            'available': availability_info['available'],
            'expected_return_date': availability_info['expected_return_date']
        })
    
    logger.info(f"[SEARCH] Completed processing all books. Returning {len(results)} results")
    
    response_data = {
        'results': results, 
        'count': len(results),
        'total': total_count,
        'offset': offset,
        'has_more': (offset + limit) < total_count
    }
    
    logger.info(f"[SEARCH] Response data size: {len(str(response_data))} characters")
    
    response = JsonResponse(response_data)
    return add_cors_headers(response)


def get_book_availability(isbn):
    """
    Get book availability status and expected return date if borrowed.
    """
    try:
        book = Book.objects.get(ISBN=isbn)
        
        # Check if there's an active or late borrow
        active_borrow = Borrow.objects.filter(
            book=book,
            status__in=['active', 'late']
        ).order_by('-last_date').first()
        
        if active_borrow:
            return {
                'available': False,
                'expected_return_date': active_borrow.last_date.strftime('%Y-%m-%d')
            }
        else:
            return {
                'available': True,
                'expected_return_date': None
            }
    except Book.DoesNotExist:
        return {
            'available': False,
            'expected_return_date': None
        }


def book_list(request):
    """
    Get all books with their availability status.
    Supports pagination with limit parameter.
    """
    # Update late borrows when listing books
    update_late_borrows()
    
    # Get pagination parameters
    try:
        limit = int(request.GET.get('limit', 50))  # Default to 50 books
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        limit = 50
        offset = 0
    
    # Limit maximum results to prevent large responses
    limit = min(limit, 100)
    
    # Get books with pagination
    books = Book.objects.all()[offset:offset + limit]
    total_count = Book.objects.count()
    
    results = []
    for book in books:
        availability_info = get_book_availability(book.ISBN)
        
        results.append({
            'isbn': book.ISBN,
            'name': book.name,
            'author': book.author,
            'publisher': book.publisher,
            'type': book.type,
            'year': book.year.strftime('%Y') if book.year else None,
            'explanation': book.explanation,
            'image': book.image,
            'status': book.status,
            'available': availability_info['available'],
            'expected_return_date': availability_info['expected_return_date']
        })
    
    response = JsonResponse({
        'results': results, 
        'count': len(results),
        'total': total_count,
        'offset': offset,
        'has_more': (offset + limit) < total_count
    })
    return add_cors_headers(response)


def check_staff_permission(request):
    """
    Check if the logged-in user is staff.
    Returns True if staff, False otherwise.
    """
    if 'user_id' not in request.session:
        return False
    
    user_type = request.session.get('user_type')
    return user_type == 'staff'


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def add_book(request):
    """
    Add a new book to the library. Staff only.
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
            required_fields = ['isbn', 'name', 'author', 'publisher', 'type']
            for field in required_fields:
                if not data.get(field):
                    response = JsonResponse({'error': f'{field} is required'}, status=400)
                    return add_cors_headers(response)
            
            # Check if book already exists
            if Book.objects.filter(ISBN=data['isbn']).exists():
                response = JsonResponse({'error': 'Book with this ISBN already exists'}, status=400)
                return add_cors_headers(response)
            
            # Parse year if provided
            year_obj = None
            if data.get('year'):
                try:
                    from datetime import datetime
                    year_obj = datetime.strptime(str(data['year']), '%Y').date()
                except ValueError:
                    response = JsonResponse({'error': 'Invalid year format. Use YYYY.'}, status=400)
                    return add_cors_headers(response)
            
            # Create new book
            book = Book.objects.create(
                ISBN=data['isbn'],
                name=data['name'],
                author=data['author'],
                publisher=data['publisher'],
                type=data['type'],
                year=year_obj,
                explanation=data.get('explanation', ''),
                image=data.get('image', ''),
                status='available'
            )
            
            response = JsonResponse({
                'success': True,
                'message': 'Book added successfully',
                'book': {
                    'isbn': book.ISBN,
                    'name': book.name,
                    'author': book.author,
                    'publisher': book.publisher,
                    'type': book.type,
                    'year': book.year.strftime('%Y') if book.year else None,
                    'explanation': book.explanation,
                    'image': book.image,
                    'status': book.status
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
def delete_book(request, isbn):
    """
    Delete a book from the library. Staff only.
    Cannot delete if book has active borrows.
    """
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        return add_cors_headers(response)
    
    if not check_staff_permission(request):
        response = JsonResponse({'error': 'Permission denied. Staff only.'}, status=403)
        return add_cors_headers(response)
    
    if request.method == 'DELETE':
        try:
            book = Book.objects.get(ISBN=isbn)
            
            # Check if book has active borrows
            active_borrows = Borrow.objects.filter(
                book=book,
                status__in=['active', 'late']
            ).count()
            
            if active_borrows > 0:
                response = JsonResponse({
                    'error': 'Cannot delete book with active borrows'
                }, status=400)
                return add_cors_headers(response)
            
            book.delete()
            
            response = JsonResponse({
                'success': True,
                'message': 'Book deleted successfully'
            })
            return add_cors_headers(response)
            
        except Book.DoesNotExist:
            response = JsonResponse({'error': 'Book not found'}, status=404)
            return add_cors_headers(response)
        except Exception as e:
            response = JsonResponse({'error': str(e)}, status=500)
            return add_cors_headers(response)
    
    response = JsonResponse({'error': 'DELETE method required'}, status=405)
    return add_cors_headers(response)


def get_book_detail(request, isbn):
    """
    Get detailed information about a specific book including full explanation and image.
    """
    try:
        book = Book.objects.get(ISBN=isbn)
        
        # Get availability information
        availability_info = get_book_availability(book.ISBN)
        
        book_data = {
            'isbn': book.ISBN,
            'name': book.name,
            'author': book.author,
            'publisher': book.publisher,
            'type': book.type,
            'year': book.year.strftime('%Y') if book.year else None,
            'explanation': book.explanation,  # Full explanation
            'image': book.image,
            'status': book.status,
            'available': availability_info['available'],
            'expected_return_date': availability_info['expected_return_date']
        }
        
        response = JsonResponse(book_data)
        return add_cors_headers(response)
        
    except Book.DoesNotExist:
        response = JsonResponse({'error': 'Book not found'}, status=404)
        return add_cors_headers(response)
    except Exception as e:
        response = JsonResponse({'error': str(e)}, status=500)
        return add_cors_headers(response)
