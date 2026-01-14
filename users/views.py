from django.contrib import messages
from django.contrib.auth import login, logout
from django.urls import reverse
from dotenv import load_dotenv
import os
import requests
import base64
from django.shortcuts import redirect
from .models import User
from .exceptions import GithubException, SocialLoginException
from rest_framework.views import APIView
from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework import status
from common.encrypt_util import encrypt_token

load_dotenv()


# 깃허브 로그인 API
class GithubCallbackView(APIView):
    def get(self, request):
        try:
            if request.user.is_authenticated:
                raise SocialLoginException("User already loggen in")
            code = request.GET.get("code", None)
            if code is None:
                raise GithubException("Can't get code")

            client_id = os.getenv("GITHUB_CLIENT_ID")
            client_secret = os.getenv("GITHUB_CLIENT_SECRET")

            token_request = requests.post(
                f"https://github.com/login/oauth/access_token?client_id={client_id}&client_secret={client_secret}&code={code}",
                headers={"Accept": "application/json"},
            )
            token_json = token_request.json()
            error = token_json.get("error", None)

            if error is not None:
                raise GithubException("Cant' get access token")

            access_token = token_json.get("access_token")
            encrypted_token = encrypt_token(access_token)  # access_token 암호화
            encoded_token = base64.urlsafe_b64encode(encrypted_token).decode(
                "utf-8"
            )  # base64 인코딩

            profile_request = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json",
                },
            )
            profile_json = profile_request.json()

            login_id = profile_json.get("id", None)
            if login_id is None:
                raise GithubException("Can't get user ID from profile_request")

            username = profile_json.get("login", None)
            if username is None:
                raise GithubException("Can't get username from profile_request")

            html_url = profile_json.get("html_url", None)
            if html_url is None:
                raise GithubException("Can't get html_url from profile_request")

            repos_url = profile_json.get("repos_url", None)
            if repos_url is None:
                raise GithubException("Can't get repos_url from profile_request")

            try:
                user = User.objects.get(login_id=login_id)
                user.access_token = encoded_token
                user.save()

            except User.DoesNotExist:
                user = User.objects.create(
                    login_id=login_id,
                    username=username,
                    html_url=html_url,
                    repos_url=repos_url,
                    access_token=encoded_token,
                )
                user.save()
                messages.success(request, f"{username} logged in with Github")

            login(request, user)
            print("LOGIN")
            return redirect("/")

        except GithubException as error:
            messages.error(request, error)
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        except SocialLoginException as error:
            messages.error(request, error)
            return Response({"error": str(error)}, status=status.HTTP_403_FORBIDDEN)


# 로그아웃 API
class LogoutView(APIView):
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        # 사용자가 로그인되어 있지 않은 경우
        if not request.user.is_authenticated:
            messages.info(request, "No user is currently logged in.")
            print("NO")
            return Response({"error": "로그인이 되어있지 않습니다."})

        # 로그아웃 실행
        logout(request)
        messages.success(request, "Successfully logged out.")
        print("YES")
        return Response(serializer.data)


# 사용자 정보 조회 API
class UserView(APIView):
    def get(self, request):
        user = request.user

        # 로그인하지 않은 유저가 요청을 보낸 경우
        if not user.is_authenticated:
            return Response({"error": "로그인이 필요합니다."}, status=401)

        serializer = UserSerializer(user)

        return Response(serializer.data)


# 로그인 상태 조회 API
class UserStatusView(APIView):
    def get(self, request):
        # 현재 요청을 보낸 사용자의 로그인 상태를 확인합니다.
        if request.user.is_authenticated:
            # 로그인된 사용자
            return Response({"status": "logged_in"}, status=status.HTTP_200_OK)
        else:
            # 로그인되지 않은 사용자
            return Response({"status": "logged_out"}, status=status.HTTP_200_OK)
