import random

from django.core.management.base import BaseCommand
from faker import Faker
from interviews.models import (
    Interview,
    Interview_Type,
    Type_Choice,
    Question,
    Answer,
    User,
    InterviewStyle,
    PositionType,
    QuestionType,
)


class Command(BaseCommand):
    help = "Generate fake interviews"

    def generate_interview(self, fake):
        random_number = random.randint(1, 100)
        user = User.objects.create(login_id=random_number)
        resume = fake.random_int(min=1, max=100)  # 임의의 이력서 ID 생성
        title = fake.sentence(nb_words=5)  # 임의의 제목 생성
        style = fake.random_element(elements=[tag.value for tag in InterviewStyle])
        position = fake.random_element(elements=[tag.value for tag in PositionType])

        return Interview.objects.create(
            user=user,
            resume=resume,
            title=title,
            style=style,
            position=position,
        )

    def generate_interview_type_and_choice(self, interview, fake):
        type_name = fake.word(ext_word_list=[tag.name for tag in QuestionType])
        interview_type = Interview_Type.objects.create(type_name=type_name)

        return Type_Choice.objects.create(
            interview=interview,
            interview_type=interview_type,
        )

    def generate_question_and_answer(self, interview, fake):
        content = fake.sentence(nb_words=7)  # 임의의 질문 생성
        question_type = fake.random_element(
            elements=[tag.value for tag in QuestionType]
        )
        question = Question.objects.create(
            interview=interview,
            content=content,
            question_type=question_type,
        )

        answer_content = fake.sentence(nb_words=7)  # 임의의 답변 생성
        record_url = fake.url()  # 임의의 URL 생성

        return Answer.objects.create(
            question=question,
            content=answer_content,
            record_url=record_url,
        )

    def handle(self, *args, **options):
        fake = Faker(["ko_KR"])

        for _ in range(10):
            interview = self.generate_interview(fake)
            self.generate_interview_type_and_choice(interview, fake)
            self.generate_question_and_answer(interview, fake)

        self.stdout.write(self.style.SUCCESS("Successfully generated fake interviews"))
