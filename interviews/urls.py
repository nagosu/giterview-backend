from django.urls import path
from .views import (
    QuestionView,
    InterviewResultView,
    InterviewProcessView,
    TaskResultView,
)

urlpatterns = [
    path("<int:id>", InterviewResultView.as_view(), name="interview-result-view"),
    path("<int:id>/questions", QuestionView.as_view(), name="question-view"),
    path(
        "<int:interview_id>/questions/<int:question_id>/process",
        InterviewProcessView.as_view(),
        name="interview-process",
    ),
    path("task-result/<str:task_id>", TaskResultView.as_view(), name="task-result"),
]
