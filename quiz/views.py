from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from .models import Question, Choice, Category
from .types import (
    CategoryListContext,
    QuizContext,
    QuizEndContext,
)


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


# quiz/views.py


def quiz_view(request: HttpRequest, category_id: int) -> HttpResponse:
    category: Category = get_object_or_404(Category, id=category_id)

    # Инициализация счёта и неправильных ответов
    if "score" not in request.session:
        request.session["score"] = 0
    if "wrong_answers" not in request.session:
        request.session["wrong_answers"] = 0
    if "asked_questions" not in request.session:
        request.session["asked_questions"] = []

    asked_questions = request.session["asked_questions"]

    # Проверка типа asked_questions
    if not isinstance(asked_questions, list):
        asked_questions = [asked_questions]
        request.session["asked_questions"] = asked_questions

    # Получаем следующий вопрос, который еще не задавался
    remaining_questions = category.questions.exclude(id__in=asked_questions)
    question: Optional[Question] = remaining_questions.order_by("?").first()

    if not question:
        # Если вопросов не осталось, заканчиваем квиз
        return redirect(reverse("quiz_end"))

    # Добавляем текущий вопрос в список заданных
    asked_questions.append(question.id)
    request.session["asked_questions"] = asked_questions

    context: QuizContext = {
        "question": question,
        "category": category,
        "score": request.session["score"],
        "wrong_answers": request.session["wrong_answers"],
        "previous_is_correct": None,
    }
    return render(request, "quiz/quiz.html", context)


def check_answer(request: HttpRequest, category_id: int) -> HttpResponse:
    choice_id: Optional[str] = request.POST.get("choice")
    if not choice_id:
        return redirect(reverse("quiz_view", args=[category_id]))

    choice: Choice = get_object_or_404(Choice, id=choice_id)
    is_correct: bool = choice.is_correct
    category: Category = get_object_or_404(Category, id=category_id)

    # Обновление счёта и неправильных ответов
    if is_correct:
        request.session["score"] += 1
    else:
        request.session["wrong_answers"] += 1

    # Проверка, достиг ли пользователь 3 неправильных ответов
    if request.session["wrong_answers"] >= 3:
        return redirect(reverse("quiz_end"))

    # Получаем список заданных вопросов
    asked_questions = request.session.get("asked_questions", [])
    if not isinstance(asked_questions, list):
        asked_questions = [asked_questions]
        request.session["asked_questions"] = asked_questions

    # Получаем следующий вопрос, исключая уже заданные
    remaining_questions = category.questions.exclude(id__in=asked_questions)
    question: Optional[Question] = remaining_questions.order_by("?").first()

    if not question:
        # Если вопросов не осталось, заканчиваем квиз
        return redirect(reverse("quiz_end"))

    # Добавляем текущий вопрос в список заданных
    asked_questions.append(question.id)
    request.session["asked_questions"] = asked_questions

    # Передаем информацию о результате предыдущего ответа
    context: QuizContext = {
        "question": question,
        "category": category,
        "score": request.session["score"],
        "wrong_answers": request.session["wrong_answers"],
        "previous_is_correct": is_correct,
    }
    return render(request, "quiz/quiz.html", context)


def quiz_end(request: HttpRequest) -> HttpResponse:
    score: int = request.session.get("score", 0)
    wrong_answers: int = request.session.get("wrong_answers", 0)
    total_questions: int = len(request.session.get("asked_questions", []))

    # Очистка сессии
    request.session.flush()

    context: QuizEndContext = {
        "score": score,
        "wrong_answers": wrong_answers,
        "total_questions": total_questions,
    }
    return render(request, "quiz/quiz_end.html", context)
