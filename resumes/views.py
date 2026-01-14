import uuid
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, serializers, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.expressions import RawSQL
from users.models import User
from .models import Resume
from .serializers import ResumeSerializer
from PyPDF2 import PdfReader
import fitz
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from io import BytesIO
from PIL import Image
from openai import OpenAI
import os
import io

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def summary_gpt(text_contents):
    contents = text_contents

    prompt = f"Your task is to generate a concise Korean summary of a developer's resume: {contents} with 300 character or less. The provided data is the extracted text from the resume. Your summary should highlight key information such as the candidate's skills, experiences, projects, and education, cs, personality. It should be clear, concise, and easy to understand. Also, try to identify and emphasize details that might make the candidate stand out from others."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        max_tokens=400,
        messages=[
            {"role": "system", "content": prompt},
        ],
    )

    return response.choices[0].message.content.strip()


class ResumeView(generics.ListCreateAPIView):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    http_method_names = ["post", "get"]

    @swagger_auto_schema(
        operation_description="이력서를 생성하고 PDF 파일을 업로드합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "file": openapi.Schema(type=openapi.TYPE_FILE, description="PDF file"),
                "user_id": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User ID"
                ),
            },
        ),
        responses={201: openapi.Response("Created", ResumeSerializer)},
    )
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        title = request.data.get("title")
        file = request.FILES.get("file")

        if not user_id or not file or not title:
            return Response(
                {"error": "img file or user ID or pdf file or title not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_content = BytesIO(file.read())
        pdf = fitz.open("pdf", file_content)
        text_contents = ""
        for page in pdf:
            text_contents += page.get_text()

        summary_contents = summary_gpt(text_contents)

        # PDF 첫 페이지를 이미지로 변환합니다.
        pix = pdf[0].get_pixmap()
        first_page = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # 이미지를 S3에 업로드하기 위해 BytesIO 객체로 변환합니다.
        image_io = BytesIO()
        first_page.save(image_io, format="JPEG")
        image_io.seek(0)  # Reset file pointer to the beginning

        # UUID를 생성하여 파일 이름을 고유하게 만듭니다.
        image_file_name = f"{uuid.uuid4().hex}.jpg"
        image_file = ContentFile(image_io.read(), image_file_name)

        # 파일을 S3에 업로드하고 가져옵니다.
        file_name = default_storage.save("imgs/" + image_file.name, image_file)
        image_url = default_storage.url(file_name)

        data = {
            "text_contents": summary_contents,
            "pre_image_url": image_url,
            "user_id": user_id,
            "title": title,
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    # 이력서 리스트 보여주는 뷰
    def get(self, request, format=None):
        user_id = request.user.id
        print(user_id)
        resumes = Resume.objects.filter(user_id=user_id, is_deleted=False)
        serializer = ResumeSerializer(resumes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 이력서 리스트 보여주는 뷰
# class ResumeList(generics.ListAPIView):
#     queryset = Resume.objects.filter(is_deleted=False)  # is_deleted가 False인 객체만 가져옵니다.
#     serializer_class = ResumeSerializer
#     http_method_names = ['get']
#
#     @swagger_auto_schema(operation_description="이력서 리스트를 반환합니다.")
#     def get(self, request, *args, **kwargs):
#
#         return super().get(request, *args, **kwargs)
# class ResumeList(APIView):
#     def get(self, request, format=None):
#         user_id = request.user.id
#         print(user_id)
#         resumes = Resume.objects.filter(user_id=user_id, is_deleted=False)
#         serializer = ResumeSerializer(resumes, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


class EmptySerializer(serializers.Serializer):
    pass


# 이력서 삭제 뷰
class ResumeDelete(generics.UpdateAPIView):
    queryset = Resume.objects.all()
    lookup_field = "id"
    serializer_class = EmptySerializer
    http_method_names = ["delete"]

    @swagger_auto_schema(operation_description="특정 이력서를 삭제합니다.")
    def delete(self, request, *args, **kwargs):
        resume = self.get_object()
        resume.is_deleted = True
        resume.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# class ResumeCreate(generics.CreateAPIView):
#     queryset = Resume.objects.all()
#     serializer_class = ResumeSerializer

# class ResumeList(generics.ListAPIView):
#     queryset = Resume.objects.all()
#     serializer_class = ResumeSerializer

# class ResumeDelete(generics.DestroyAPIView):
#     queryset = Resume.objects.all()
#     lookup_field = 'id'  # URL에서 삭제할 Resume의 id를 가져옵니다.
