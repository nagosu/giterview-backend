import os
import json
import boto3

from dotenv import load_dotenv

load_dotenv()


class AWSManager:
    _session = None
    _secretsmanager_client = None
    _s3_client = None
    _comprehend_client = None

    _region_name = os.getenv("REGION_NAME")

    @classmethod
    def get_session(cls):
        if not cls._session:
            cls._session = boto3.Session()

            if cls._session.region_name is None:
                cls._session = boto3.Session(
                    region_name=cls._region_name,
                    aws_access_key_id=os.getenv("AWS_SECRET_ACCESS_KEY"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_SECRET_KEY"),
                )

        return cls._session

    @classmethod
    def get_secret(cls, secret_name):
        if cls._region_name is not None:
            if cls._secretsmanager_client is None:
                session = cls.get_session()
                cls._secretsmanager_client = session.client(
                    service_name="secretsmanager"
                )

            get_secret_value_response = cls._secretsmanager_client.get_secret_value(
                SecretId=secret_name
            )
            return json.loads(get_secret_value_response["SecretString"])
        else:
            return {
                key[len(secret_name) + 1 :]: value
                for key, value in os.environ.items()
                if key.startswith(secret_name + "_")
            }

    @classmethod
    def get_s3_client(cls):
        if cls._s3_client is None:
            session = cls.get_session()
            secrets = cls.get_secret("s3")
            cls._s3_client = session.client(
                "s3",
                aws_access_key_id=secrets["access_key"],
                aws_secret_access_key=secrets["secret_key"],
            )
        return cls._s3_client

    @classmethod
    def get_comprehend_client(cls):
        if cls._comprehend_client is None:
            session = cls.get_session()
            cls._comprehend_client = session.client("comprehend")
        return cls._comprehend_client
