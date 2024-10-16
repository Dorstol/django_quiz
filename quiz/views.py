from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404

from .models import Question, Choice, Category
from .types import (CategoryListContext, QuizContex, CheckAnswerContext, NoQuestionContext, )


def category_list(request: HttpRequest) -> HttpResponse:
    categories = Category.objects.all()
    context: CategoryListContext = {
        "categories": categories,
    }
    return render(
        request,
        "quiz/category_list.html",
        context,
    )


def quiz_view(request: HttpRequest, category_id: int) -> HttpResponse:
    category = get_object_or_404(
        Category,
        id=category_id,
    )
    question = Question.objects.order_by("?").first()
    if not question:
        context: NoQuestionContext = {'category': category}
        return render(
            request,
            "quiz/categories_list.html",
            context,
        )
    context: QuizContex = {
        "question": question,
        "category": category,
    }
    return render(
        request,
        "quiz/quiz.html",
        context,
    )


def check_answer(request: HttpRequest, category_id: int) -> HttpResponse:
    choice_id: Optional[str] = request.POST.get(
        "choice",
    )
    choice = get_object_or_404(
        Choice,
        id=choice_id,
    )
    is_correct: bool = choice.is_correct
    category = get_object_or_404(
        Category,
        id=category_id,
    )
    context: CheckAnswerContext = {
        "is_correct": is_correct,
        "category": category,
    }
    return render(
        request,
        "quiz/result.html",
        context,
    )
