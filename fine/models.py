from django.db import models
from user.models import Staff, Student

# Create your models here.
class Fine(models.Model):
    Fine_ID = models.AutoField(primary_key=True)

    Staff_ID = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='fines_as_staff')
    Student_ID = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fines_as_student')

    Date = models.DateField()

    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    )
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    Amount = models.FloatField()
