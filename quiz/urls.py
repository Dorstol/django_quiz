from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz_view, name='quiz_view'),
    path('check_answer/', views.check_answer, name='check_answer'),
]
