from enum import Enum
from django.db import models
from common.models import BaseModel
from users.models import User
from resumes.models import Resume


class InterviewStyle(Enum):
    VIDEO = "video"
    VOICE = "voice"
    TEXT = "text"


class PositionType(Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"


class QuestionType(Enum):
    PROJECT = "project"
    CS = "cs"
    PERSONALITY = "personality"
    COMMON = "common"


class Interview(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    style = models.CharField(
        max_length=5, choices=[(tag.value, tag.name) for tag in InterviewStyle]
    )
    position = models.CharField(
        max_length=9, choices=[(tag.value, tag.name) for tag in PositionType]
    )


class Interview_Type(models.Model):
    type_name = models.CharField(max_length=20)


class Type_Choice(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    interview_type = models.ForeignKey(Interview_Type, on_delete=models.CASCADE)


class Question(BaseModel):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    content = models.CharField(max_length=500)
    question_type = models.CharField(
        max_length=11, choices=[(tag.value, tag.name) for tag in QuestionType]
    )


class Answer(BaseModel):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    content = models.CharField(max_length=500)
    record_url = models.URLField(max_length=500)


class Repository(BaseModel):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    repo_name = models.CharField(max_length=255)
    repo_summary = models.TextField()
