# Generated by Django 4.1.1 on 2022-10-12 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Clue",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("clue", models.CharField(max_length=20, verbose_name="clue")),
            ],
        ),
        migrations.RenameModel(old_name="Words", new_name="Word",),
    ]