# Generated by Django 4.2.7 on 2023-11-19 18:26

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="job",
            options={"ordering": ("-created_at",)},
        ),
    ]
