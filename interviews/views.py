import json
import tempfile
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from django.core.exceptions import ObjectDoesNotExist
from .models import Answer, Interview, Question
from .serializers import (
    QuestionListSerializer,
    AnswerCreateSerializer,
    InterviewResultSerializer,
    InterviewListSerializer,
    InterviewCreateSerializer,
    QuestionCreateSerializer,
)
from openai import OpenAI
from .utils import handle_uploaded_file_s3
import boto3
from botocore.exceptions import NoCredentialsError
from celery_worker.tasks import process_interview
from celery.result import AsyncResult

from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# 면접 질문 목록 조회 API
class QuestionView(APIView):
    def get(self, request, id):
        try:
            interview = Interview.objects.get(id=id)
            serializer = QuestionListSerializer(interview)

            return Response(serializer.data)

        except ObjectDoesNotExist:
            return Response(
                {"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND
            )


class InterviewProcessView(APIView):
    def post(self, request, interview_id, question_id, *args, **kwargs):
        request.data["question"] = question_id
        request.data["interview"] = interview_id
        serializer = AnswerCreateSerializer(data=request.data)
        if serializer.is_valid():
            is_last = request.data.get("is_last", False)

            record_file = request.FILES.get("record_url")

            if record_file is None:
                return Response(
                    {"error": "No audio file provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            temp_file_path = tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3"
            ).name

            with open(temp_file_path, "wb") as file:
                for chunk in record_file.chunks():
                    file.write(chunk)

            request.data["record_url"] = None

            task = process_interview.delay(request.data, temp_file_path, is_last)

            return Response(
                {"task_id": task.id, "wait_time": 2000}, status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskResultView(APIView):
    def get(self, request, task_id):
        user_id = request.user.id
        print("user_id", user_id)

        task = AsyncResult(task_id)

        total_delay = 4
        num_checks = 2  # check 2 per 1s
        delay = total_delay / num_checks

        for _ in range(num_checks):
            task_done = task.ready()
            if task_done:
                result = task.get()

                if result is not None:
                    # keyword = result["keyword"]
                    pass
                else:
                    return Response(
                        "bing_api error", status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                response_data = task.get()

                return Response(response_data, status=status.HTTP_200_OK)

            # await asyncio.sleep(delay)

        return Response(
            status=status.HTTP_202_ACCEPTED,
        )  # status code 수정


# 질문 생성 API
class QuestionCreateView(APIView):
    def post(self, request, id, *args, **kwargs):
        data = request.data
        data["interview"] = id  # interview_id를 request.data에 추가
        serializer = QuestionCreateSerializer(data=data)
        if serializer.is_valid():
            created_questions = serializer.save()
            for question in created_questions:
                serializer = QuestionCreateSerializer(question)  # 개별 객체를 직렬화
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 면접 결과 조회 API
class InterviewResultView(APIView):
    def get(self, request, id):
        try:
            interview = Interview.objects.get(id=id)
            serializer = InterviewResultSerializer(interview)

            return Response(serializer.data)

        except ObjectDoesNotExist:
            return Response(
                {"error": "object not found"}, status=status.HTTP_404_NOT_FOUND
            )


class InterviewView(APIView):
    # 면접 목록 조회 API
    def get(self, request):
        user_id = request.user.id

        # user의 모든 interview를 조회
        interviews = Interview.objects.filter(user=user_id)

        # question이 있고 question과 answer의 개수가 일치하는 interview만 filter
        valid_interviews = []
        for interview in interviews:
            questions = Question.objects.filter(interview=interview)
            if not questions.exists():
                interview.is_deleted = True  # 질문이 없으면 is_deleted를 true로 설정
                interview.save()
                continue

            # 모든 question에 대한 answer이 있는지 확인
            all_answered = all(
                Answer.objects.filter(question=question).exists()
                for question in questions
            )
            if all_answered:  # 모든 question에 대한 answer이 있는 경우
                valid_interviews.append(interview)
            else:
                interview.is_deleted = (
                    True  # 모든 질문에 대한 답변이 없으면 is_deleted를 true로 설정
                )
                interview.save()

        serializer = InterviewListSerializer(valid_interviews, many=True)

        return Response(serializer.data)

    # 면접 생성 API
    def post(self, request):
        serializer = InterviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
