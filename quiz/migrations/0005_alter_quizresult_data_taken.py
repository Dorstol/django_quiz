# Generated by Django 5.1.2 on 2024-11-11 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0004_alter_quizresult_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="quizresult",
            name="data_taken",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
