import os
import uuid
import redis
import boto3
import asyncio
import logging
import concurrent

from .celery import app

from uuid import uuid4
from openai import OpenAI
from django.core.files import File
from botocore.exceptions import NoCredentialsError
from interviews.utils import handle_uploaded_file_s3
from interviews.serializers import AnswerCreateSerializer, QuestionCreateSerializer

MAX_CONCURRENT_REQUESTS = 3

redis_client = redis.StrictRedis(host="redis", port=6379, db=2)

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

app.conf.update({"worker_concurrency": MAX_CONCURRENT_REQUESTS})

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# Whisper API로 오디오를 텍스트로 변환하는 메소드
def transcribe(audio_file):
    transcript = client.audio.transcriptions.create(
        model="whisper-1", file=audio_file, response_format="text"
    )

    # transcript가 비어있는 경우 처리
    if len(transcript.strip()) <= 3:
        transcript = "올바른 답변 부탁드립니다."  # 기본값 설정

    print(transcript)
    return transcript


@app.task(bind=True)
def process_interview(self, data, temp_file_path, is_last):
    try:
        with open(temp_file_path, "rb") as temp_file:
            record_file = File(temp_file)

            # 음성 파일을 text로 변환
            content = transcribe(temp_file)[:500]
            record_file.seek(0)

            data["record_url"] = record_file

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(handle_uploaded_file_s3, record_file)

                serializer = AnswerCreateSerializer(data=data)
                if serializer.is_valid():
                    if temp_file:
                        answer = serializer.save(content=content)

                    if is_last:
                        record_url, _ = future.result()
                        answer.record_url = record_url
                        answer.save()
                        return {}

                    question_serializer = QuestionCreateSerializer(data=data)
                    if question_serializer.is_valid():
                        created_questions = question_serializer.save()
                        question_serializer = QuestionCreateSerializer(
                            created_questions, many=True
                        )
                        answer_serializer = AnswerCreateSerializer(answer)

                        record_url, _ = future.result()
                        answer.record_url = record_url
                        answer.save()

                        return {
                            "answer": answer_serializer.data,
                            "question": question_serializer.data,
                        }
                    else:
                        raise ValueError(question_serializer.errors)
                else:
                    raise ValueError(serializer.errors)
    except Exception as e:
        self.update_state(state="FAILURE")
        raise ValueError("Some condition is not met. " + str(e))
    finally:
        os.remove(temp_file_path)
