import base64
import requests
from rest_framework import serializers
from .models import Interview_Type, Question, Interview, Type_Choice, Answer, Repository
from .utils import create_questions_withgpt, save_question
import openai
import os
from openai import OpenAI
from common.encrypt_util import decrypt_token

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# 면접 결과 조회 Serializer
class InterviewResultSerializer(serializers.ModelSerializer):
    repo_names = serializers.SerializerMethodField()
    interview_type_names = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            "title",
            "interview_type_names",
            "position",
            "style",
            "resume",
            "repo_names",
            "questions",
            "answers",
        ]

    def get_repo_names(self, obj):
        repositories = Repository.objects.filter(interview=obj)
        return [repo.repo_name for repo in repositories]

    def get_interview_type_names(self, obj):
        type_choices = Type_Choice.objects.filter(interview=obj)
        if type_choices.exists():
            return [tc.interview_type.type_name for tc in type_choices]
        return []

    def get_questions(self, obj):
        questions_list_serializer = QuestionListSerializer(instance=obj)
        return questions_list_serializer.get_questions(obj)

    def get_answers(self, obj):
        questions = Question.objects.filter(interview=obj)
        answers = Answer.objects.filter(question__in=questions)
        return [
            {"content": answer.content, "record_url": answer.record_url}
            for answer in answers
        ]


# 질문 목록 조회 Serializer
class QuestionListSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = ["questions"]

    def get_questions(self, obj):
        questions = Question.objects.filter(interview=obj)
        return [
            {
                "id": question.id,
                "type_name": self.get_type_name_for_question(question),
                "content": question.content,
            }
            for question in questions
        ]

    def get_type_name_for_question(self, question):
        return question.question_type


# 면접 답변 등록 Serializer
class AnswerCreateSerializer(serializers.ModelSerializer):
    record_url = serializers.FileField()  # FileField를 사용하여 파일 객체를 받습니다.

    class Meta:
        model = Answer
        fields = ["question", "record_url"]

    # def create(self, validated_data):
    #   record_file = validated_data.pop('record_url')

    #   # AWS S3를 사용하는 경우
    #   # record_url = handle_uploaded_file_s3(record_file)

    #   # record_url을 다시 설정
    #   validated_data['record_url'] = record_url

    #   return super().create(validated_data)
    # #Response에 변환된 url 보여주기
    # def to_representation(self, instance):
    #   ret = super().to_representation(instance)
    #   ret['record_url'] = instance.record_url  # 변환된 URL로 변경
    #   return ret


# 면접 목록 조회 Serializer
class InterviewListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Interview
        fields = ["id", "title", "created_at"]


# 면접 생성 Serializer
class InterviewCreateSerializer(serializers.ModelSerializer):
    repo_names = serializers.ListField(
        child=serializers.CharField(max_length=200), write_only=True
    )
    type_names = serializers.ListField(
        child=serializers.CharField(max_length=200), write_only=True
    )

    repo_names_display = serializers.SerializerMethodField()
    type_names_display = serializers.SerializerMethodField()

    resume = serializers.IntegerField(write_only=True)

    class Meta:
        model = Interview
        fields = [
            "id",
            "user",
            "title",
            "position",
            "style",
            "resume",
            "repo_names",
            "type_names",
            "repo_names_display",
            "type_names_display",
        ]

    def create(self, validated_data):
        type_names = validated_data.pop("type_names", None)
        resume_id = validated_data.pop("resume", None)
        repo_names = validated_data.pop("repo_names", None)
        user = validated_data.get("user")
        if not user:
            raise serializers.ValidationError("User must be provided")

        # User 테이블에서 access_token을 가져옴
        encoded_token = user.access_token
        encrypted_token = base64.urlsafe_b64decode(encoded_token)  # base64 디코딩
        decrypted_token = decrypt_token(encrypted_token)  # access_token 복호화
        if not decrypted_token:
            raise serializers.ValidationError("User does not have an access token")

        interview = Interview.objects.create(resume_id=resume_id, **validated_data)

        repo_summary = []
        file_contents = []

        if user:
            username = user.username

            for repo_name in repo_names:
                file_content = self.get_repo_file_content(
                    username, repo_name, decrypted_token
                )
                file_contents.extend(file_content)

        # repository에서 추출한 파일 내용을 gpt로 요약
        if file_contents:
            prompt = f"{file_contents} Summarize the main technology stacks and major libraries of this code in English words. List them only in words."

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                temperature=0.5,
                max_tokens=400,
                messages=[
                    {"role": "system", "content": prompt},
                ],
            )
            repo_summary.append(response.choices[0].message.content.strip())

        if repo_names:
            repo_summary_str = "\n".join(repo_summary)  # 리스트를 문자열로 변환
            print(repo_summary_str)
            for name in repo_names:
                Repository.objects.create(
                    interview=interview, repo_name=name, repo_summary=repo_summary_str
                )

        if type_names:
            for name in type_names:
                type_obj, created = Interview_Type.objects.get_or_create(type_name=name)
                Type_Choice.objects.create(interview=interview, interview_type=type_obj)

        question = "간단한 자기소개 부탁드립니다."
        Question.question_type = "common"
        Question.objects.create(
            content=question, question_type=Question.question_type, interview=interview
        )

        return interview

    # username과 repo_name을 이용해 파일 내용을 추출하는 함수
    def get_repo_file_content(self, username, repo_name, access_token):
        headers = {"Authorization": f"token {access_token}"}
        search_url = f"https://api.github.com/search/code?q=filename:package.json+OR+filename:build.gradle+OR+filename:pom.xml+OR+filename:requirements.txt+OR+filename:Gemfile+OR+filename:packages.config+OR+filename:composer.json+OR+filename:go.mod+repo:{username}/{repo_name}"
        search_response = requests.get(search_url, headers=headers)
        if search_response.status_code == 200:
            items = search_response.json().get("items", [])
            file_contents = []

            for item in items:
                file_url = item.get("url")
                if file_url:
                    file_details_response = requests.get(file_url)
                    if file_details_response.status_code == 200:
                        download_url = file_details_response.json().get("download_url")
                        if download_url:
                            file_content_response = requests.get(download_url)
                            if file_content_response.status_code == 200:
                                file_contents.append(file_content_response.text)

            return file_contents

        return None

    def create_interviews(self, validated_data):
        interview = Interview.objects.create(**validated_data)
        return interview

    def create_repo(self, repo_names, interview):
        for repo_name in repo_names:
            Repository.objects.create(repo_name=repo_name, interview=interview)

    def create_type_name(self, type_names, interview):
        for type_name in type_names:
            interview_type, created = Interview_Type.objects.get_or_create(
                type_name=type_name
            )
            type_choice, created = Type_Choice.objects.get_or_create(
                interview=interview, interview_type=interview_type
            )
            if not created:
                type_choice.interview = interview
                type_choice.save()

    def get_repo_names_display(self, obj):
        return [repo.repo_name for repo in obj.repository_set.all()]

    def get_type_names_display(self, obj):
        return [
            type_choice.interview_type.type_name
            for type_choice in obj.type_choice_set.all()
        ]


# 질문 생성
class QuestionCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)  # id 필드를 읽기 전용으로 설정
    interview = serializers.PrimaryKeyRelatedField(queryset=Interview.objects.all())
    question_type = serializers.CharField()

    class Meta:
        model = Question
        fields = ["id", "interview", "question_type"]

    def create(self, validated_data):
        interview = validated_data["interview"]
        type_name = validated_data["question_type"]

        questions = create_questions_withgpt(interview, type_name)

        # 생성된 Question 객체를 저장할 리스트
        created_questions = []

        for question, question_type in questions:
            question_obj = Question.objects.create(
                content=question, question_type=question_type, interview=interview
            )
            created_questions.append(question_obj)

        # 생성된 Question 객체들을 반환
        return created_questions

    def to_representation(self, instance):
        # super().to_representation(instance)를 호출하여 기본 직렬화 데이터를 가져옵니다.
        ret = super().to_representation(instance)
        # 직렬화 데이터에 content 필드를 추가합니다.
        ret["content"] = instance.content
        return ret
