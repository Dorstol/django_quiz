from django.db import models


class Question(models.Model):
    text = models.CharField(max_length=255)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='questions')

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Category(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name
