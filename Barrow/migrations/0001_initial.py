
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("Books", "0001_initial"),
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Borrow",
            fields=[
                ("Borrow_ID", models.AutoField(primary_key=True, serialize=False)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("late", "Late"),
                            ("returned", "Returned"),
                        ],
                        max_length=20,
                    ),
                ),
                ("date", models.DateField()),
                ("last_date", models.DateField()),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="borrows",
                        to="Books.book",
                    ),
                ),
                (
                    "staff",
                    models.ForeignKey(
                        limit_choices_to={"role": "staff"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="handled_borrows",
                        to="user.staff",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        limit_choices_to={"role": "member"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="student_borrows",
                        to="user.student",
                    ),
                ),
            ],
        ),
    ]
