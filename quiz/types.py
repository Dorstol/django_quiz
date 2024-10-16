from typing import TypedDict, List

from .models import Category, Question


class CategoryListContext(TypedDict):
    categories: List[Category]


class QuizContex(TypedDict):
    category: Category
    question: Question


class CheckAnswerContext(TypedDict):
    is_correct: bool
    category: Category


class NoQuestionContext(TypedDict):
    category: Category
