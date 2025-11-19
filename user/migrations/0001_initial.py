
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("User_ID", models.AutoField(primary_key=True, serialize=False)),
                ("Name", models.CharField(max_length=50)),
                ("Email", models.CharField(max_length=50)),
                ("Phone", models.CharField(max_length=10)),
                ("Username", models.CharField(max_length=50)),
                ("Password", models.CharField(max_length=50)),
                (
                    "Type",
                    models.CharField(
                        choices=[("student", "Student"), ("staff", "Staff")],
                        max_length=10,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Staff",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="user.user",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="user.user",
                    ),
                ),
            ],
        ),
    ]
