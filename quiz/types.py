from typing import TypedDict, List, Optional

from django import forms

from .models import Category, Question


class BaseContext(TypedDict):
    category: Category


class CategoryListContext(TypedDict):
    categories: List[Category]


class QuizContext(BaseContext):
    question: Question
    score: int
    wrong_answers: int
    previous_is_correct: Optional[bool]


class CheckAnswerContext(BaseContext):
    is_correct: bool
    score: int
    wrong_answers: int


class NoQuestionsContext(BaseContext):
    pass


class QuizEndContext(TypedDict):
    score: int
    wrong_answers: int
    total_questions: int
    form: forms.Form
