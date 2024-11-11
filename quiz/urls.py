from django.urls import path
from . import views

urlpatterns = [
    path("", views.category_list, name="category_list"),
    path("quiz/<int:category_id>/", views.quiz_view, name="quiz_view"),
    path(
        "quiz/<int:category_id>/check_answer/", views.check_answer, name="check_answer"
    ),
    path("quiz/end", views.quiz_end, name="quiz_end"),
]
