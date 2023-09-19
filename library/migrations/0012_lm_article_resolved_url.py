# Generated by Django 4.2.2 on 2023-06-06 03:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0011_delete_lm_remove_article_resolved_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="LM",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("excerpt", models.TextField(default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.AddField(
            model_name="article",
            name="resolved_url",
            field=models.CharField(default="", max_length=256),
            preserve_default=False,
        ),
    ]
