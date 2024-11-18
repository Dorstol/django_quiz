from datetime import timedelta
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from .forms import QuizResultForm
from .models import Question, Choice, Category, QuizResult
from .types import (
    CategoryListContext,
    QuizContext,
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
    request.session["category_id"] = category_id
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
    score = request.session.get('score', 0)
    wrong_answers = request.session.get('wrong_answers', 0)
    total_questions = len(request.session.get('asked_questions', []))
    category_id = request.session.get('category_id')

    # Получаем категорию
    category = None
    if category_id:
        category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = QuizResultForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']

            try:
                # Проверяем, существует ли уже запись с таким email
                quiz_result = QuizResult.objects.get(email=email)
                # Проверяем, прошло ли достаточно времени с последнего обновления
                time_since_last_update = timezone.now() - quiz_result.data_taken
                if time_since_last_update < timedelta(hours=1):
                    # Если прошло меньше часа, не обновляем и возвращаем сообщение
                    form.add_error(None, 'Вы можете обновлять результат не чаще, чем раз в час.')
                    context = {
                        'form': form,
                        'score': score,
                        'wrong_answers': wrong_answers,
                        'total_questions': total_questions,
                    }
                    return render(request, 'quiz/partials/quiz_end_form.html', context)
                # Обновляем имя, если оно изменилось
                if quiz_result.name != name:
                    quiz_result.name = name
                # Обновляем результат, если новый результат выше
                if score > quiz_result.score:
                    quiz_result.score = score
                quiz_result.date_taken = timezone.now()
                quiz_result.category = category
                quiz_result.save()
            except QuizResult.DoesNotExist:
                # Если запись не существует, создаем новую
                quiz_result = form.save(commit=False)
                quiz_result.score = score
                quiz_result.category = category
                quiz_result.save()
            # Очистка сессии
            request.session.flush()
            # Возвращаем частичный шаблон с таблицей рейтинга
            top_results = QuizResult.objects.order_by('-score', 'data_taken')[:10]
            context = {'top_results': top_results}
            return render(request, 'quiz/partials/leaderboard_partial.html', context)
        else:
            # Если форма не валидна, возвращаем частичный шаблон с формой и ошибками
            context = {
                'form': form,
                'score': score,
                'wrong_answers': wrong_answers,
                'total_questions': total_questions,
            }
            return render(request, 'quiz/partials/quiz_end_form.html', context)
    else:
        form = QuizResultForm()
        context = {
            'score': score,
            'wrong_answers': wrong_answers,
            'total_questions': total_questions,
            'form': form,
        }
        return render(request, 'quiz/quiz_end.html', context)


def leaderboard_partial(request: HttpRequest) -> HttpResponse:
    top_results = QuizResult.objects.order_by("-score", "data_taken")
    from django.db.models import Max

    top_results = (
        top_results.values("email", "name")
        .annotate(max_score=Max("score"), data_taken=Max("data_taken"))
        .order_by("-max_score", "data_taken")[:10]
    )

    context = {"top_results": top_results}
    return render(request, "quiz/partials/leaderboard_partial.html", context=context)
