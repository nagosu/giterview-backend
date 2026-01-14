from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()

key_string = os.getenv("CRYPTOGRAPHY_KEY")
key = key_string.encode()

# Fernet 인스턴스 생성
cipher_suite = Fernet(key)


# 암호화 함수
def encrypt_token(token):
    return cipher_suite.encrypt(token.encode())


# 복호화 함수
def decrypt_token(encrypted_token):
    return cipher_suite.decrypt(encrypted_token).decode()
