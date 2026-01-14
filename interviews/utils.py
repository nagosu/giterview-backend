import boto3
from uuid import uuid4
from botocore.exceptions import NoCredentialsError
import openai
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from openai import OpenAI
import os
import time
import interviews
from interviews.models import QuestionType, Question, Interview, Repository, Answer
from resumes.models import Resume
import requests


def get_github_file_content(username, repo_name):
    url = f"https://api.github.com/search/code?q=filename:package.json+OR+filename:build.gradle+repo:{username}/{repo_name}"
    response = requests.get(url)
    if response.status_code == 200:
        items = response.json().get("items", [])
        if items:
            file_url = items[0].get("url")
            file_response = requests.get(file_url)
            if file_response.status_code == 200:
                download_url = file_response.json().get("download_url")
                download_response = requests.get(download_url)
                print(download_response)
                return download_response
    return None


def handle_uploaded_file_s3(file):

    s3_client = boto3.client("s3")
    bucket_name = "resume7946"  # 여기에 실제 버킷 이름을 넣어주세요.
    file_key = "answer_audio/" + str(uuid4()) + ".mp3"  # mp3로 저장되면 mp3로 바꾸기

    try:
        s3_client.upload_fileobj(file, bucket_name, file_key)
        file_url = f"https://{bucket_name}.s3.ap-northeast-2.amazonaws.com/{file_key}"

        return file_url, file_key
    except NoCredentialsError:
        return {"error": "S3 credential is missing"}


api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def create_questions_withgpt(interview, type_names):
    try:
        # Resume 테이블에서 resume_id에 해당하는 레코드를 가져옵니다.
        resume = Resume.objects.get(id=interview.resume_id)
        # 이력서의 text_contents를 가져옵니다.
        resume_contents = resume.text_contents
        # GPT 함수에 resume_contents를 전달합니다.
        # question_types = [qt.value for qt in QuestionType if qt.value in type_names]
        question_type = type_names

        # Repository 테이블에서 interview_id에 해당하는 레코드를 가져옵니다.
        repository = Repository.objects.filter(interview=interview.id)

        # Repository 객체에서 repo_name을 가져옵니다.
        repo_names = []
        repo_infos = []
        for repo in repository:
            repo_name = repo.repo_name
            repo_info = repo.repo_summary
            repo_names.append(repo_name)
            repo_infos.append(repo_info)

        if len(repo_infos) == 1:
            formatted_info = repo_infos[0].replace("\n", "")
            formatted_name = repo_names[0].replace("\n", "")
        else:
            formatted_info = ", ".join(repo_infos).replace("\n", "")
            formatted_name = ", ".join(repo_names).replace("\n", "")

        previous_question = (
            Question.objects.filter(interview=interview.id).order_by("-id").first()
        )
        previous_answer = Answer.objects.filter(question=previous_question.id).first()

        position = interview.position

        questions = []

        previous_question_type = previous_question.question_type
        # 현재 질문타입 꺼내기

        if previous_question_type == question_type:
            print("same")
            # 전 질문타입과 같다면 꼬리질문 가능
            if question_type == "project":
                print("project")
                # 프로젝트 질문
                prompt = f"Your task is to role-play as a developer interviewer and ask a project-related interview question in Korean, within the limit of 200 characters. Question related to the candidate's project experience such as project overview, difficulties and solutions, lessons learned, roles, implemented features should be based on the GitHub-{formatted_info} and resume-{resume_contents}. If you think the previous answer:{previous_answer} is okay, make a tail question and if not, make a new one with a different content than the previous one. The tail questions that deepen and apply previous answer:{previous_answer} should be unique and not repeat previous questions. They should explore different aspects of the candidate's experience, skills, and understanding of the project. Questions should be direct and natural. It should sound like a real person is asking the question but refrain from including greetings or personal sentiments, intention, emotion. do not say anything outside of the question and use the word '지원자분' instead of name. The output should not include any additional information or counters such as the character count of the question"

            elif question_type == "cs":
                print("cs")
                # cs질문
                prompt = f"Your task is to role-play as a company's CS expert and interviewer. Ask a natural and flowing question in Korean, within the limit of 200 characters. If you think the previous answer:{previous_answer} is okay, make a tail question and if not, make a new one with a different content than the previous one. The tail question should continue naturally from the situation in the previous answer: {previous_answer}, and must present a new problem situation that differs from the previous question. Questions should be direct and natural, and proposes a specific and extreme situation. This situation should be something that could realistically occur within the {position} role. The question should be about the specific concept, understanding, operation, and implementation of a single topic among Data Structures and Algorithms, Operating Systems, Networks, Databases, System Design, Software Engineering, Programming Language, etc. It should sound like a real person is asking the question but refrain from including greetings or personal sentiments, intention, emotion. do not say anything outside of the question and use the word '지원자분' instead of name."

            else:
                print("person")
                # 인성질문
                prompt = f"You're participating as both the company's HR representative and the interviewer. Your task is to ask one interview question in Korean within the limit of 200 characters. If you think the previous answer:{previous_answer.content} is okay, make a tail question and if not, make a new one with a different content than the previous one. The tail question should continue naturally from the situation in the previous answer: {previous_answer.content}, and must present a new problem situation that differs from the previous question. Questions should be direct and natural, and proposes a specific and extreme situation. This situation should be something that could realistically occur within the {position} role, and it should test the candidate's teamwork skills, problem-solving abilities, and character under stress. It should sound like a real person is asking the question but refrain from including greetings or personal sentiments, intention, emotion. do not say anything outside of the question and use the word '지원자분' instead of name. The output should not include any additional information or counters such as the character count of the question"

        else:
            # 전 질문타임과 다르거나 두번째 질문이라면 꼬리질문 불가능
            print("different")

            if question_type == "project":
                print("project")
                # 프로젝트 질문
                prompt = f"You're participating as developer interviewer. Your task is to ask one developer project-question in Korean, within the limit of 200 characters. Question related to the candidate's project experience such as project overview, difficulties and solutions, lessons learned, roles, implemented features should be based on the GitHub-{formatted_info} and resume-{resume_contents}. Questions should be direct and natural. It should sound like a real person is asking the question but refrain from including greetings or personal sentiments, intention, emotion. do not say anything outside of the question. and use the word '지원자분' instead of name."

            elif question_type == "cs":
                print("cs")
                # cs질문
                # prompt = f"Your task is to role-play as a company's CS expert and interviewer. Ask a natural and flowing question in Korean, within the limit of 200 characters. The question should be based on the {', '.join(repo_names)}:{', '.join(repo_infos)}, {resume_contents}, and {position}, and should be related to computer science topics such as Data Structures and Algorithms,Operating Systems,Networks,Databases,System Design,Software Engineering,Specific Technology Stacks. Questions should be direct and natural. The question should sound like a real person is asking but refrain from including greetings or personal sentiments, intention, emotion. do not say anything outside of the question and use the word '지원자분' instead of name. The output should not include any additional information or counters such as the character count of the question"
                prompt = f"Your task is to role-play as a company's CS expert and interviewer. Ask a natural and flowing question in Korean, within the limit of 200 characters. The question should be about the specific concept, understanding, operation, and implementation of a single topic among Data Structures and Algorithms, Operating Systems, Networks, Databases, System Design, Software Engineering, Programming Language, etc and based on {position}. Questions should be direct and natural. The question should sound like a real person is asking but refrain from including greetings or personal sentiments, intention, emotion. Do not say anything outside of the question and use the word '지원자분' instead of name."

            else:
                print("person")
                # 인성질문
                prompt = f"You're participating as both the company's HR representative and the interviewer. Your task is to ask one interview question that proposes a specific and extreme situation in Korean within the limit of 200 characters. This situation should be something that could realistically occur within the {position} role, and it should test the candidate's teamwork skills, problem-solving abilities, and character under stress. Questions should be direct and natural. It should sound like a real person is asking the question but refrain from including greetings or personal sentiments, intention, emotion. Do not say anything outside of the question and refer to the candidate as '지원자분' instead of using their name. The output should not include any additional information or counters such as the character count of the question."

        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            temperature=0.5,
            frequency_penalty=1,
            presence_penalty=-1,
            max_tokens=400,
            n=1,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"I want you to ask me a only one type developer interview question. Instead do not tell me the number of characters. Don't mention the my answer as it is",
                },
            ],
        )
        questions.append((response.choices[0].message.content.strip(), question_type))

    except Exception as e:
        return Response("Failed to create questions with GPT: " + str(e))
    return questions


def save_question(questions, interview):
    for question, question_type in questions:
        Question.objects.create(
            content=question, question_type=question_type, interview=interview
        )
