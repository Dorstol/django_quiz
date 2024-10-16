from django.db import models


class Question(models.Model):
    text: models.CharField = models.CharField(
        max_length=255,
    )
    category: models.ForeignKey = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="questions",
    )

    def __str__(self) -> str:
        return self.text


class Choice(models.Model):
    question: models.ForeignKey = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    text: models.CharField = models.CharField(
        max_length=255,
    )
    is_correct: models.BooleanField = models.BooleanField(
        default=False,
    )

    def __str__(self) -> str:
        return self.text


class Category(models.Model):
    name: models.CharField = models.CharField(
        max_length=64,
        unique=True,
    )

    def __str__(self) -> str:
        return self.name
