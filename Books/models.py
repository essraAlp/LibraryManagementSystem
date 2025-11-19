from django.db import models

# Create your models here.
class Book(models.Model):
    ISBN = models.IntegerField(primary_key=True)  # int PK
    name = models.CharField(max_length=50)
    explanation = models.CharField(max_length=150)
    publisher = models.CharField(max_length=50)
    author = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    year = models.DateField()  # EER'deki "date" ile uyumlu
    image = models.CharField(max_length=100)  # URL/path
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('late', 'Late'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
