from django.db import models
from user.models import Staff, Student
from Books.models import Book

# Create your models here.
class Borrow(models.Model):
    Borrow_ID = models.AutoField(primary_key=True)
    # Staff_ID → staff user
    staff = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,   # staff silinirse borç kaydı bozulmasın
        related_name="handled_borrows",
        limit_choices_to={'role': 'staff'}
    )
    # Student_ID → member user
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,   # öğrenci silinemez (aktif borrow varsa)
        related_name="student_borrows",
        limit_choices_to={'role': 'member'}
    )
    # Book_ISBN
    book = models.ForeignKey(
        Book,
        to_field='ISBN',
        on_delete=models.PROTECT,   # kitap borrowed ise silinemez
        related_name="borrows"
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('late', 'Late'),
        ('returned', 'Returned'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    # Date (Borrow Date)
    date = models.DateField()      # ödünç alma tarihi
    # Last_Date (Due Date)
    last_date = models.DateField() # teslim edilmesi gereken son gün