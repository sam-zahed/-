import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL','postgresql://postgres:postgres@localhost:5432/fastapi_agent')
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT','http://localhost:9000')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY','minioadmin')
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY','minioadmin')
