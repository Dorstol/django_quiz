from django.contrib import admin
from .models import Question, Choice, Category


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ["text", "category"]


admin.site.register(Question, QuestionAdmin)
admin.site.register(Category)
