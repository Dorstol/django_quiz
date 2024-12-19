from datetime import timedelta
from typing import Optional

from django.db.models import Max
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from .forms import QuizResultForm
from .models import Question, Choice, Category, QuizResult
from .types import CategoryListContext, QuizContext


def category_list(request: HttpRequest) -> HttpResponse:
    categories = Category.objects.all()
    context: CategoryListContext = {
        "categories": categories,
    }
    return render(request, "quiz/category_list.html", context)


def init_quiz_session(request: HttpRequest, category_id: int) -> None:
    """Инициализирует сессию для прохождения квиза."""
    request.session["category_id"] = category_id
    request.session["score"] = 0
    request.session["wrong_answers"] = 0
    request.session["asked_questions"] = []


def get_next_question(category: Category, asked_questions: list[int]) -> Optional[Question]:
    """Возвращает следующий случайный вопрос из категории, который ещё не задавался."""
    remaining_questions = category.questions.exclude(id__in=asked_questions)
    return remaining_questions.order_by("?").first()


def quiz_view(request: HttpRequest, category_id: int) -> HttpResponse:
    category = get_object_or_404(Category, id=category_id)

    # Если квиз запускается первый раз или пользователь начал заново,
    # инициализируем сессию
    if "category_id" not in request.session or request.session.get("category_id") != category_id:
        init_quiz_session(request, category_id)

    asked_questions = request.session.get("asked_questions", [])
    if not isinstance(asked_questions, list):
        asked_questions = []
        request.session["asked_questions"] = asked_questions

    # Проверяем, есть ли в категории вопросы
    if not category.questions.exists():
        # Нет вопросов - сразу конец квиза
        return redirect(reverse("quiz_end"))

    # Получаем следующий вопрос
    question = get_next_question(category, asked_questions)
    if not question:
        # Если вопросов не осталось
        return redirect(reverse("quiz_end"))

    # Добавляем текущий вопрос в список уже заданных
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
    choice_id = request.POST.get("choice")
    if not choice_id:
        return redirect(reverse("quiz_view", args=[category_id]))

    choice = get_object_or_404(Choice, id=choice_id)
    category = get_object_or_404(Category, id=category_id)

    # Обновление счёта
    if choice.is_correct:
        request.session["score"] = request.session.get("score", 0) + 1
    else:
        request.session["wrong_answers"] = request.session.get("wrong_answers", 0) + 1

    # Проверка предела неправильных ответов
    if request.session["wrong_answers"] >= 3:
        return redirect(reverse("quiz_end"))

    asked_questions = request.session.get("asked_questions", [])
    if not isinstance(asked_questions, list):
        asked_questions = []
        request.session["asked_questions"] = asked_questions

    # Получаем следующий вопрос
    question = get_next_question(category, asked_questions)
    if not question:
        return redirect(reverse("quiz_end"))

    asked_questions.append(question.id)
    request.session["asked_questions"] = asked_questions

    context: QuizContext = {
        "question": question,
        "category": category,
        "score": request.session.get("score", 0),
        "wrong_answers": request.session.get("wrong_answers", 0),
        "previous_is_correct": choice.is_correct,
    }
    return render(request, "quiz/quiz.html", context)


def quiz_end(request: HttpRequest) -> HttpResponse:
    score = request.session.get("score", 0)
    wrong_answers = request.session.get("wrong_answers", 0)
    asked_questions = request.session.get("asked_questions", [])
    total_questions = len(asked_questions)
    category_id = request.session.get("category_id")

    category = None
    if category_id:
        category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        form = QuizResultForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            name = form.cleaned_data["name"]

            try:
                quiz_result = QuizResult.objects.get(email=email)
                time_since_last_update = timezone.now() - quiz_result.data_taken
                if time_since_last_update < timedelta(hours=1):
                    # Менее часа прошло с последнего обновления
                    form.add_error(None, "Вы можете обновлять результат не чаще, чем раз в час.")
                    context = {
                        "form": form,
                        "score": score,
                        "wrong_answers": wrong_answers,
                        "total_questions": total_questions,
                    }
                    return render(request, "quiz/partials/quiz_end_form.html", context)
                # Обновляем данные
                if quiz_result.name != name:
                    quiz_result.name = name
                if score > quiz_result.score:
                    quiz_result.score = score
                quiz_result.date_taken = timezone.now()
                quiz_result.category = category
                quiz_result.save()
            except QuizResult.DoesNotExist:
                # Создаём новый результат
                quiz_result = form.save(commit=False)
                quiz_result.score = score
                quiz_result.category = category
                quiz_result.save()

            # Очистка сессии после сохранения результата
            request.session.flush()

            # Показываем таблицу рейтинга
            top_results = (
                QuizResult.objects
                .values("email", "name")
                .annotate(max_score=Max("score"), data_taken=Max("data_taken"))
                .order_by("-max_score", "data_taken")[:10]
            )
            return render(request, "quiz/partials/leaderboard_partial.html", {"top_results": top_results})
        else:
            # Ошибки валидации формы
            context = {
                "form": form,
                "score": score,
                "wrong_answers": wrong_answers,
                "total_questions": total_questions,
            }
            return render(request, "quiz/partials/quiz_end_form.html", context)
    else:
        form = QuizResultForm()
        context = {
            "score": score,
            "wrong_answers": wrong_answers,
            "total_questions": total_questions,
            "form": form,
        }
        return render(request, "quiz/quiz_end.html", context)


def leaderboard_partial(request: HttpRequest) -> HttpResponse:
    top_results = (
        QuizResult.objects
        .values("email", "name")
        .annotate(max_score=Max("score"), data_taken=Max("data_taken"))
        .order_by("-max_score", "data_taken")[:10]
    )
    return render(request, "quiz/partials/leaderboard_partial.html", {"top_results": top_results})
