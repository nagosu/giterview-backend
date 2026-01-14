from django.core.management.base import BaseCommand
from faker import Faker
from resumes.models import Resume


class Command(BaseCommand):
    help = "Generate fake resumes"

    def handle(self, *args, **options):
        fake = Faker(["ko_KR"])

        for _ in range(10):
            Resume.objects.create(
                user_id=fake.random_int(min=1, max=100),  # 임의의 사용자 ID 생성
                image_url=fake.image_url(),  # 임의의 이미지 URL 생성
                text_contents=fake.text(),  # 임의의 텍스트 생성
            )

        self.stdout.write(self.style.SUCCESS("Successfully generated fake resumes"))
