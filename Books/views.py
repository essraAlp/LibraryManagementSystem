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

def add_cors_headers(response):
    """Add CORS headers to response"""
    response['Access-Control-Allow-Origin'] = 'http://localhost:8080'
    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
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
    
    return JsonResponse({
        'results': results, 
        'count': len(results),
        'total': total_count,
        'offset': offset,
        'has_more': (offset + limit) < total_count
    })
    return add_cors_headers(response)
