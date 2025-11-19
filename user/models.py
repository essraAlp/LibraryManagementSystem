from django.db import models

# Create your models here.
class User(models.Model):
    USER_TYPES = (
        ('student', 'Student'),
        ('staff', 'Staff'),
    )

    User_ID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Email = models.CharField(max_length=50)
    Phone = models.CharField(max_length=10)
    Username = models.CharField(max_length=50)
    Password = models.CharField(max_length=50)

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
