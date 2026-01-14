from django.db import models
from common.models import BaseModel


class Resume(BaseModel):
    # id = models.AutoField(primary_key=True)  # 이력서 ID
    user_id = models.CharField(max_length=500)  # 사용자 ID
    pre_image_url = models.URLField(max_length=500)  # 미리보기 이미지 URL
    text_contents = models.TextField()  # 텍스트 추출내용
    title = models.CharField(max_length=255)  # 이력서 제목

    class Meta:
        db_table = "resumes"
