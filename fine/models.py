from django.db import models
from user.models import Staff, Student
from Barrow.models import Borrow

# Create your models here.
class Fine(models.Model):
    Fine_ID = models.AutoField(primary_key=True)

    Staff_ID = models.ForeignKey(Staff, on_delete=models.SET_NULL, related_name='fines_as_staff', null=True, blank=True)
    Student_ID = models.ForeignKey(Student, on_delete=models.SET_NULL, related_name='fines_as_student', null=True, blank=True)
    Borrow_ID = models.ForeignKey(Borrow, on_delete=models.SET_NULL, related_name='fines', null=True, blank=True)

    Date = models.DateField()

    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    )
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    Payment_Date = models.DateField(null=True, blank=True)

    Amount = models.FloatField()
