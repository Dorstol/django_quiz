from django.shortcuts import render, get_object_or_404
from .models import Question, Choice


def quiz_view(request):
    question = Question.objects.order_by('?').first()
    return render(request, 'quiz/quiz.html', {'question': question})


def check_answer(request):
    choice_id = request.POST.get('choice')
    choice = get_object_or_404(Choice, id=choice_id)
    is_correct = choice.is_correct
    return render(request, 'quiz/result.html', {'is_correct': is_correct})

