from django.urls import path
from . import views
from .views import ResumeDelete

urlpatterns = [
    path("delete/<int:id>", ResumeDelete.as_view(), name="resume-delete"),
]
