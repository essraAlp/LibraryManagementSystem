from django.db import models

# Create your models here.
class User(models.Model):
    USER_TYPES = (
        ('student', 'Student'),
        ('staff', 'Staff'),
    )

    User_ID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Email = models.CharField(max_length=50, unique=True)
    Phone = models.CharField(max_length=10, unique=True)
    Username = models.CharField(max_length=50, unique=True)
    Password = models.CharField(max_length=128)  # Increased for hashed passwords

    Type = models.CharField(max_length=10, choices=USER_TYPES)

    def __str__(self):
        return f"{self.Name} ({self.Type})"
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return f"Student: {self.user.Name}"

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return f"Staff: {self.user.Name}"
